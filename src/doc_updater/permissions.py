"""Permission handler: restrict writes to the docs repo only."""

from __future__ import annotations

from .config import Config

SENSITIVE_PATTERNS = [".env", "credentials", "secret", ".ssh", ".key", ".pem"]


def create_permission_handler(config: Config):
    """Build a can_use_tool callback that enforces write boundaries."""
    docs_repo = str(config.docs_repo_path)

    async def can_use_tool(
        tool_name: str,
        input_data: dict,
        context: dict,
    ):
        # Import here to avoid top-level SDK dependency issues in tests
        from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

        # Write/Edit only allowed in docs repo
        if tool_name in ("Write", "Edit"):
            file_path = input_data.get("file_path", "")
            if not file_path.startswith(docs_repo):
                return PermissionResultDeny(
                    message=(
                        f"Write/Edit only allowed in docs repo ({docs_repo}). "
                        f"Attempted: {file_path}"
                    ),
                )

            # Block writes to sensitive files
            if any(p in file_path.lower() for p in SENSITIVE_PATTERNS):
                return PermissionResultDeny(
                    message=f"Cannot write to sensitive file: {file_path}",
                )

        return PermissionResultAllow(updated_input=input_data)

    return can_use_tool
