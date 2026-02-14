"""Safety hooks: block dangerous commands and audit-log tool usage."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

from .config import Config

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "sudo rm",
    "> /dev/sda",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
]


async def block_dangerous_bash(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Block bash commands matching dangerous patterns."""
    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked dangerous pattern: {pattern}"
                    ),
                }
            }
    return {}


async def audit_log(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Log all tool invocations to stderr for debugging."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    preview = str(tool_input)[:200]
    print(f"  [{timestamp}] {tool_name}: {preview}", file=sys.stderr)
    return {}


def create_safety_hooks(config: Config) -> dict:
    """Build the hooks dict for ClaudeAgentOptions."""
    hooks: dict[str, list] = {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [block_dangerous_bash]},
        ],
    }
    if config.verbose:
        hooks["PreToolUse"].append({"hooks": [audit_log]})
    return hooks
