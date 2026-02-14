"""Terminal output formatting and progress reporting."""

from __future__ import annotations

import sys

MAX_OUTPUT_LINES = 8
MAX_LINE_WIDTH = 100


def print_phase(title: str) -> None:
    """Print a phase header."""
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"  {title}", file=sys.stderr)
    print(f"{'=' * 60}\n", file=sys.stderr)


def print_progress(message: str) -> None:
    """Print a progress message."""
    print(f"  ... {message}", file=sys.stderr)


def print_result(message: str) -> None:
    """Print a result summary."""
    print(f"\n  >> {message}\n", file=sys.stderr)


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"\n  !! ERROR: {message}\n", file=sys.stderr)


def print_command(command: str) -> None:
    """Print a command being executed, prominently formatted."""
    if len(command) > MAX_LINE_WIDTH:
        command = command[: MAX_LINE_WIDTH - 3] + "..."
    print(f"\n  $ {command}", file=sys.stderr)


def print_command_output(output: str) -> None:
    """Print truncated, indented command output."""
    if not output or not output.strip():
        print("    (no output)", file=sys.stderr)
        return

    lines = output.strip().splitlines()
    total = len(lines)
    shown = lines[:MAX_OUTPUT_LINES]

    for line in shown:
        if len(line) > MAX_LINE_WIDTH:
            line = line[: MAX_LINE_WIDTH - 3] + "..."
        print(f"    {line}", file=sys.stderr)

    if total > MAX_OUTPUT_LINES:
        print(f"    ... ({total - MAX_OUTPUT_LINES} more lines)", file=sys.stderr)

    print(file=sys.stderr)
