"""CLI entry point for doc-updater."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doc-updater",
        description="Automatically update developer documentation from source code",
    )

    parser.add_argument(
        "--code-repo",
        type=Path,
        required=True,
        help="Path to the source code repository",
    )
    parser.add_argument(
        "--docs-repo",
        type=Path,
        required=True,
        help="Path to the documentation repository",
    )
    parser.add_argument(
        "--doc-files",
        nargs="+",
        default=["docs/getting-started.md"],
        help="Documentation files to update (relative to docs repo)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config file (overrides CLI args where specified)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum update-verify iterations (default: 3)",
    )
    parser.add_argument(
        "--docker-image",
        type=str,
        default=None,
        help="Docker base image for verification (e.g., python:3.11-slim)",
    )
    parser.add_argument(
        "--no-docker",
        action="store_true",
        help="Disable Docker; use temp directory for verification",
    )
    parser.add_argument(
        "--verification-instructions",
        type=Path,
        default=None,
        help=(
            "Path to a file containing custom verification instructions. "
            "These replace the default Docker/tmpdir environment description "
            "in the verifier's prompt. Use this when verification requires "
            "custom hardware, specific network access, or non-standard setup."
        ),
    )
    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help=(
            "High-level context about what changed or where to focus. "
            "E.g., 'We migrated from pip to uv' or "
            "'The database setup section is broken'."
        ),
    )
    parser.add_argument(
        "--context-file",
        type=Path,
        default=None,
        help=(
            "Path to a file containing context about what changed. "
            "Use instead of --context for longer notes."
        ),
    )
    parser.add_argument(
        "--create-pr",
        action="store_true",
        default=False,
        help="Automatically create a GitHub PR (requires gh CLI)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed agent activity",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="opus",
        choices=["sonnet", "opus", "haiku"],
        help="Claude model to use (default: opus)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    from .config import Config
    from .orchestrator import run_pipeline

    config = Config.from_args(args)

    result = asyncio.run(run_pipeline(config))

    # Print summary
    print(f"\nStatus: {result.final_status}")
    print(f"Iterations used: {result.iterations_used}")
    if result.pr_diff:
        preview = result.pr_diff[:2000]
        if len(result.pr_diff) > 2000:
            preview += "\n... (truncated)"
        print(f"\nDiff preview:\n{preview}")
