"""Main pipeline: analyze code → update docs → verify → iterate."""

from __future__ import annotations

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
    ResultMessage,
    TextBlock,
)

from .agents import (
    create_code_analyzer_agent,
    create_doc_updater_agent,
    create_doc_verifier_agent,
)
from .config import Config
from .hooks import create_safety_hooks
from .models import PipelineResult
from .output import print_error, print_phase, print_progress, print_result
from .permissions import create_permission_handler
from .tools import create_custom_tools_server


async def _collect_result(client: ClaudeSDKClient) -> str:
    """Consume messages from the client until a ResultMessage, return text."""
    texts: list[str] = []
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    texts.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.result:
                texts.append(message.result)
            break
    return "\n".join(texts)


def _verification_passed(result_text: str) -> bool:
    """Check if the verification result indicates a pass."""
    lower = result_text.lower()
    # Look for explicit pass indicators in the JSON output
    if '"overall_status": "pass"' in lower or '"overall_status":"pass"' in lower:
        return True
    # Heuristic fallback: no "fail" verdict found
    if '"overall_status": "fail"' in lower or '"overall_status":"fail"' in lower:
        return False
    # If we can't parse it, assume failure to be safe
    return False


async def run_pipeline(config: Config) -> PipelineResult:
    """Run the three-phase documentation update pipeline."""

    custom_server = create_custom_tools_server(config)

    agents = {
        "code-analyzer": create_code_analyzer_agent(config),
        "doc-updater": create_doc_updater_agent(config),
        "doc-verifier": create_doc_verifier_agent(config),
    }

    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a documentation maintenance orchestrator. You coordinate "
            "three specialist agents to analyze code, update documentation, and "
            "verify the results. Always invoke the appropriate subagent for each "
            "phase. Do not perform analysis, writing, or verification yourself."
        ),
        allowed_tools=[
            "Read", "Bash", "Glob", "Grep",
            "Task",
            "mcp__doctools__setup_verification_env",
            "mcp__doctools__teardown_verification_env",
            "mcp__doctools__create_git_branch",
            "mcp__doctools__get_git_diff",
        ],
        agents=agents,
        mcp_servers={"doctools": custom_server},
        hooks=create_safety_hooks(config),
        can_use_tool=create_permission_handler(config),
        permission_mode="acceptEdits",
        cwd=str(config.code_repo_path),
        add_dirs=[str(config.docs_repo_path)],
        max_turns=50,
        model=config.model,
    )

    analysis_result = ""
    update_result = ""
    verify_result = ""
    pr_diff = ""
    iterations_used = 0

    try:
        async with ClaudeSDKClient(options=options) as client:
            # ── PHASE 1: Code Analysis ──
            print_phase("Phase 1: Analyzing codebase")
            analysis_prompt = (
                f"Use the code-analyzer agent to analyze the codebase at "
                f"{config.code_repo_path}. Read the README and all relevant "
                f"source files to produce a complete analysis report."
            )
            if config.user_context:
                analysis_prompt += (
                    f"\n\nIMPORTANT CONTEXT FROM THE DEVELOPER:\n"
                    f"{config.user_context}\n\n"
                    f"Pay special attention to the areas mentioned above."
                )
            await client.query(analysis_prompt)
            analysis_result = await _collect_result(client)
            print_progress("Analysis complete")

            # ── PHASE 2 + 3 LOOP ──
            verification_failure_context = ""
            for iteration in range(config.max_iterations):
                iterations_used = iteration + 1

                # Phase 2: Update docs
                print_phase(
                    f"Phase 2: Updating documentation (iteration {iterations_used})"
                )
                update_prompt = (
                    f"Use the doc-updater agent to update the documentation files "
                    f"in {config.docs_repo_path} based on the analysis report above."
                )
                if config.user_context:
                    update_prompt += (
                        f"\n\nDEVELOPER CONTEXT (prioritize these areas):\n"
                        f"{config.user_context}"
                    )
                if verification_failure_context:
                    update_prompt += (
                        f"\n\nPREVIOUS VERIFICATION FAILED. Here is the failure "
                        f"report that must be addressed:\n"
                        f"{verification_failure_context}"
                    )

                if config.dry_run:
                    update_prompt += (
                        "\n\nDRY RUN MODE: Show what changes you would make "
                        "but do NOT actually write any files."
                    )

                await client.query(update_prompt)
                update_result = await _collect_result(client)
                print_progress("Documentation updated")

                # Phase 3: Verify docs
                print_phase(
                    f"Phase 3: Verifying documentation (iteration {iterations_used})"
                )

                verify_prompt = (
                    f"Use the doc-verifier agent to verify the documentation by "
                    f"following every step in a clean environment. Execute each "
                    f"command exactly as written and report results."
                )

                if config.use_docker and config.docker_image:
                    verify_prompt = (
                        f"First, set up a verification environment using the "
                        f"setup_verification_env tool with base_image "
                        f"'{config.docker_image}'. Then {verify_prompt.lower()} "
                        f"After verification, tear down the environment."
                    )

                await client.query(verify_prompt)
                verify_result = await _collect_result(client)

                if _verification_passed(verify_result):
                    print_result("Verification PASSED")
                    break
                else:
                    print_result(
                        f"Verification FAILED (iteration {iterations_used})"
                    )
                    verification_failure_context = verify_result
            else:
                print_result(
                    f"Max iterations ({config.max_iterations}) reached. "
                    f"Creating PR with best-effort documentation."
                )

            # ── CREATE BRANCH + DIFF ──
            if not config.dry_run:
                print_phase("Creating branch and diff")
                await client.query(
                    f"Use the create_git_branch tool to create a branch named "
                    f"'docs/auto-update' in {config.docs_repo_path} with commit "
                    f"message 'docs: auto-update setup documentation'. "
                    f"Then use get_git_diff to show the changes."
                )
                pr_diff = await _collect_result(client)
                print_progress("Branch created")

                if config.create_pr:
                    print_phase("Creating pull request")
                    await client.query(
                        f"Create a GitHub pull request from the current branch "
                        f"in {config.docs_repo_path} using the gh CLI. "
                        f"Title: 'docs: auto-update setup documentation'. "
                        f"Include a summary of all changes in the PR body."
                    )
                    pr_result_text = await _collect_result(client)
                    print_result(f"PR created:\n{pr_result_text}")

    except CLINotFoundError:
        print_error(
            "Claude Code CLI not found. "
            "Install with: pip install claude-agent-sdk"
        )
        raise SystemExit(1)
    except ProcessError as e:
        print_error(f"Agent process failed (exit code {e.exit_code}): {e.stderr}")
        raise SystemExit(2)
    except CLIJSONDecodeError as e:
        print_error(f"Failed to parse agent output: {e.line}")
        raise SystemExit(3)
    except ClaudeSDKError as e:
        print_error(f"SDK error: {e}")
        raise SystemExit(4)

    final_status = "verified" if _verification_passed(verify_result) else "best_effort"

    return PipelineResult(
        analysis=analysis_result,
        update=update_result,
        verification=verify_result,
        pr_diff=pr_diff,
        iterations_used=iterations_used,
        final_status=final_status,
    )
