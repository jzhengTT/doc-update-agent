"""AgentDefinition factory functions for all three subagents."""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition

from .config import Config
from .prompts import (
    build_code_analyzer_prompt,
    build_doc_updater_prompt,
    build_doc_verifier_prompt,
)


def create_code_analyzer_agent(config: Config) -> AgentDefinition:
    """Subagent that reads the codebase and produces an analysis report."""
    return AgentDefinition(
        description=(
            "Analyzes a source code repository to extract information needed for "
            "developer documentation: dependencies, setup steps, build commands, "
            "environment variables, configuration files, and project structure."
        ),
        prompt=build_code_analyzer_prompt(
            code_repo_path=str(config.code_repo_path),
        ),
        tools=["Read", "Grep", "Glob", "Bash"],
        model="opus",
    )


def create_doc_updater_agent(config: Config) -> AgentDefinition:
    """Subagent that updates documentation files based on an analysis report."""
    return AgentDefinition(
        description=(
            "Updates developer setup/getting-started documentation based on a "
            "code analysis report. Writes clear, step-by-step guides with "
            "verified commands. Works in the documentation repository."
        ),
        prompt=build_doc_updater_prompt(
            docs_repo_path=str(config.docs_repo_path),
            target_doc_files=config.target_doc_files,
        ),
        tools=["Read", "Write", "Edit", "Glob", "Grep"],
        model="opus",
    )


def create_doc_verifier_agent(
    config: Config,
    verification_env_id: str | None = None,
) -> AgentDefinition:
    """Subagent that follows documentation step-by-step to verify correctness."""
    return AgentDefinition(
        description=(
            "Verifies developer documentation by following setup instructions "
            "step-by-step in a clean environment. Reports exactly which steps "
            "succeed and which fail."
        ),
        prompt=build_doc_verifier_prompt(
            doc_file_paths=config.target_doc_files,
            verification_env=config.verification_env,
            verification_env_id=verification_env_id,
            custom_instructions=config.verification_instructions,
        ),
        tools=["Read", "Bash", "Grep", "Glob"],
        model="opus",
    )
