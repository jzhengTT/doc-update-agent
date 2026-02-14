"""Data contracts for inter-phase communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Dependency:
    name: str
    version_constraint: str
    purpose: str


@dataclass
class EnvVariable:
    name: str
    required: bool
    description: str
    example_value: str


@dataclass
class SetupStep:
    order: int
    command: str
    description: str
    expected_output: str | None = None
    working_directory: str | None = None


@dataclass
class AnalysisReport:
    project_name: str
    language: str
    framework: str
    description: str
    system_requirements: list[str]
    dependencies: list[Dependency]
    env_variables: list[EnvVariable]
    setup_steps: list[SetupStep]
    build_commands: list[str]
    run_commands: list[str]
    test_commands: list[str]
    docker_available: bool
    additional_notes: list[str]


@dataclass
class VerificationStep:
    step_number: int
    command: str
    status: Literal["pass", "fail", "unclear", "skipped"]
    actual_output: str
    expected_output: str | None = None
    error_message: str | None = None


@dataclass
class VerificationResult:
    overall_status: Literal["pass", "fail"]
    steps: list[VerificationStep]
    environment_info: str
    suggestions: list[str]
    consecutive_failures: int


@dataclass
class DocChange:
    file_path: str
    change_type: Literal["created", "modified", "deleted"]
    summary: str


@dataclass
class PipelineResult:
    analysis: str
    update: str
    verification: str
    pr_diff: str
    iterations_used: int = 1
    final_status: Literal["verified", "best_effort", "failed"] = "verified"


# JSON schemas for subagent output formatting

ANALYSIS_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_name": {"type": "string"},
        "language": {"type": "string"},
        "framework": {"type": "string"},
        "description": {"type": "string"},
        "system_requirements": {"type": "array", "items": {"type": "string"}},
        "dependencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version_constraint": {"type": "string"},
                    "purpose": {"type": "string"},
                },
                "required": ["name", "version_constraint", "purpose"],
            },
        },
        "env_variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "required": {"type": "boolean"},
                    "description": {"type": "string"},
                    "example_value": {"type": "string"},
                },
                "required": ["name", "required", "description", "example_value"],
            },
        },
        "setup_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "order": {"type": "integer"},
                    "command": {"type": "string"},
                    "description": {"type": "string"},
                    "expected_output": {"type": ["string", "null"]},
                    "working_directory": {"type": ["string", "null"]},
                },
                "required": ["order", "command", "description"],
            },
        },
        "build_commands": {"type": "array", "items": {"type": "string"}},
        "run_commands": {"type": "array", "items": {"type": "string"}},
        "test_commands": {"type": "array", "items": {"type": "string"}},
        "docker_available": {"type": "boolean"},
        "additional_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "project_name",
        "language",
        "framework",
        "description",
        "system_requirements",
        "dependencies",
        "env_variables",
        "setup_steps",
        "build_commands",
        "run_commands",
        "test_commands",
        "docker_available",
        "additional_notes",
    ],
}

VERIFICATION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_status": {"type": "string", "enum": ["pass", "fail"]},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "command": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pass", "fail", "unclear", "skipped"],
                    },
                    "actual_output": {"type": "string"},
                    "expected_output": {"type": ["string", "null"]},
                    "error_message": {"type": ["string", "null"]},
                },
                "required": [
                    "step_number",
                    "command",
                    "status",
                    "actual_output",
                ],
            },
        },
        "environment_info": {"type": "string"},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "consecutive_failures": {"type": "integer"},
    },
    "required": [
        "overall_status",
        "steps",
        "environment_info",
        "suggestions",
        "consecutive_failures",
    ],
}
