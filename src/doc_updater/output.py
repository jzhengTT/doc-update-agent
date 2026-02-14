"""Terminal output formatting and progress reporting."""

from __future__ import annotations

import sys


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
