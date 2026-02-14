"""Configuration loading from CLI args and optional YAML file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


@dataclass
class Config:
    code_repo_path: Path
    docs_repo_path: Path
    target_doc_files: list[str]
    max_iterations: int = 3
    docker_image: str | None = None
    use_docker: bool = True
    create_pr: bool = False
    dry_run: bool = False
    verbose: bool = False
    model: str = "opus"
    verification_env: Literal["docker", "tmpdir", "custom"] = "docker"
    verification_instructions: str | None = None
    user_context: str | None = None

    @classmethod
    def from_args(cls, args) -> Config:
        """Build config from CLI args, optionally overlaying YAML config."""
        config_dict: dict = {}

        if args.config and Path(args.config).exists():
            with open(args.config) as f:
                config_dict = yaml.safe_load(f) or {}

        use_docker = not args.no_docker

        # Load custom verification instructions from file if provided
        verification_instructions: str | None = None
        vi_path = args.verification_instructions or config_dict.get(
            "verification_instructions"
        )
        if vi_path:
            verification_instructions = Path(vi_path).read_text().strip()

        # Load user context (inline or from file)
        user_context: str | None = None
        if args.context_file and Path(args.context_file).exists():
            user_context = Path(args.context_file).read_text().strip()
        elif args.context:
            user_context = args.context

        # Determine verification environment type
        if verification_instructions:
            verification_env = "custom"
        elif use_docker:
            verification_env = "docker"
        else:
            verification_env = "tmpdir"

        return cls(
            code_repo_path=Path(args.code_repo).resolve(),
            docs_repo_path=Path(args.docs_repo).resolve(),
            target_doc_files=args.doc_files,
            max_iterations=args.max_iterations,
            docker_image=args.docker_image or config_dict.get("docker_image"),
            use_docker=use_docker,
            create_pr=args.create_pr,
            dry_run=args.dry_run,
            verbose=args.verbose,
            model=args.model,
            verification_env=verification_env,
            verification_instructions=verification_instructions,
            user_context=user_context,
        )
