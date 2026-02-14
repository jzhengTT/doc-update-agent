"""Custom MCP tools for Docker environment management and git operations."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from .config import Config


@tool(
    "setup_verification_env",
    "Create a clean Docker container or temp directory for verifying documentation steps",
    {"base_image": str, "working_dir": str},
)
async def setup_verification_env(args: dict[str, Any]) -> dict[str, Any]:
    """Spin up a Docker container or create a temp directory for verification."""
    base_image = args.get("base_image", "ubuntu:22.04")
    working_dir = args.get("working_dir", "/workspace")

    try:
        result = subprocess.run(
            [
                "docker", "run", "-d", "--rm",
                "-w", working_dir,
                base_image, "sleep", "3600",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            container_id = result.stdout.strip()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "type": "docker",
                            "container_id": container_id,
                            "working_dir": working_dir,
                        }),
                    }
                ]
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: temp directory
    tmpdir = tempfile.mkdtemp(prefix="doc-verify-")
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"type": "tmpdir", "path": tmpdir}),
            }
        ]
    }


@tool(
    "teardown_verification_env",
    "Clean up the verification environment (stop Docker container or remove temp directory)",
    {"env_type": str, "env_id": str},
)
async def teardown_verification_env(args: dict[str, Any]) -> dict[str, Any]:
    """Stop Docker container or remove temp directory."""
    env_type = args["env_type"]
    env_id = args["env_id"]

    if env_type == "docker":
        subprocess.run(
            ["docker", "stop", env_id],
            capture_output=True,
            timeout=30,
        )
    elif env_type == "tmpdir":
        shutil.rmtree(env_id, ignore_errors=True)

    return {"content": [{"type": "text", "text": "Environment cleaned up."}]}


@tool(
    "create_git_branch",
    "Create a new git branch in a repository and stage all changes",
    {"repo_path": str, "branch_name": str, "commit_message": str},
)
async def create_git_branch(args: dict[str, Any]) -> dict[str, Any]:
    """Create a branch, stage all changes, and commit."""
    repo = args["repo_path"]
    branch = args["branch_name"]
    message = args.get("commit_message", "docs: auto-update documentation")

    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Branch '{branch}' created and committed.\n{result.stdout}",
            }
        ]
    }


@tool(
    "get_git_diff",
    "Get the git diff of all changes in the current branch compared to the base branch",
    {"repo_path": str, "base_branch": str},
)
async def get_git_diff(args: dict[str, Any]) -> dict[str, Any]:
    """Return the diff between current branch and base."""
    repo = args["repo_path"]
    base = args.get("base_branch", "main")

    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return {
        "content": [
            {"type": "text", "text": result.stdout or "(no changes)"}
        ]
    }


def create_custom_tools_server(config: Config):
    """Build the MCP server with all custom tools."""
    return create_sdk_mcp_server(
        name="doctools",
        version="1.0.0",
        tools=[
            setup_verification_env,
            teardown_verification_env,
            create_git_branch,
            get_git_diff,
        ],
    )
