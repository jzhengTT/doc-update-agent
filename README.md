# doc-updater

Automatically update developer documentation based on changes in your codebase.

doc-updater is a CLI agent that reads your source code, updates setup/getting-started guides in a separate docs repo, then verifies the documentation by following it step-by-step. If verification fails, it iterates — fixing the docs and re-verifying until they're correct.

## How it works

```
Phase 1: Analyze codebase + README
    |
    v
Phase 2: Update docs in docs repo  <--- retry with failure context
    |                                      |
    v                                      |
Phase 3: Verify docs step-by-step  --------+  (up to 3 iterations)
    |
    v  (pass)
Create branch / PR in docs repo
```

1. **Code Analyzer** reads your codebase and README to understand dependencies, setup steps, env variables, build commands, etc.
2. **Doc Updater** compares the analysis against your existing docs and updates them.
3. **Doc Verifier** follows the updated docs exactly as a new developer would, executing each command and reporting pass/fail per step.

If verification fails, the failure report is fed back to the updater, which fixes the broken steps and re-verifies.

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (bundled with `claude-agent-sdk`)

## Installation

```bash
git clone <this-repo>
cd doc-update-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Set your API key:

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Quick start

```bash
python -m doc_updater \
  --code-repo /path/to/your/app \
  --docs-repo /path/to/your/docs
```

This will analyze the code repo, update `docs/getting-started.md` in the docs repo, verify the changes, and create a git branch with the result.

## Usage

```
python -m doc_updater [OPTIONS]
```

### Required flags

| Flag | Description |
|------|-------------|
| `--code-repo PATH` | Path to the source code repository |
| `--docs-repo PATH` | Path to the documentation repository |

### Optional flags

| Flag | Default | Description |
|------|---------|-------------|
| `--doc-files FILE [FILE ...]` | `docs/getting-started.md` | Documentation files to update (relative to docs repo) |
| `--context TEXT` | | High-level hint about what changed or where to focus |
| `--context-file PATH` | | Same as `--context` but reads from a file (for longer notes) |
| `--verification-instructions PATH` | | Custom instructions for the verification step (see below) |
| `--docker-image IMAGE` | | Docker image for verification (e.g., `python:3.11-slim`) |
| `--no-docker` | `false` | Use a temp directory instead of Docker for verification |
| `--max-iterations N` | `3` | Max update-verify retry cycles |
| `--create-pr` | `false` | Create a GitHub PR after updating (requires `gh` CLI) |
| `--dry-run` | `false` | Show what would change without writing files |
| `--verbose` | `false` | Show detailed agent activity and audit logs |
| `--model MODEL` | `opus` | Claude model to use (`opus`, `sonnet`, or `haiku`) |
| `--config PATH` | | Path to a YAML config file |

## Examples

### Basic update

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs
```

### Tell the agent what changed

Use `--context` to give the agent a hint about what to focus on:

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --context "We migrated from pip to uv, and the Redis setup section is broken"
```

For longer notes, use `--context-file`:

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --context-file ./change-notes.txt
```

Where `change-notes.txt` might contain:

```
Recent changes:
- Switched from Flask to FastAPI in v2.0
- Database moved from SQLite to PostgreSQL
- The "Environment Setup" section still references the old .env.example format
- New dependency: redis>=7.0 (used for caching, not documented yet)
```

### Verify with Docker

Run verification in an isolated Docker container:

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --docker-image python:3.11-slim
```

### Custom verification instructions

If verification requires custom hardware or a non-standard environment, provide a file with specific instructions:

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --verification-instructions ./verify-instructions.md \
  --no-docker
```

Where `verify-instructions.md` describes how to run verification on your setup:

```
This project must be verified on the local FPGA development board.

1. Ensure the Xilinx toolchain is available: run `vivado -version`
2. Connect to the board via JTAG: run `hw_server` in the background
3. All build commands must target the ZCU104 board profile
4. After flashing, verify output on serial port /dev/tty.usbserial-210
5. Use `minicom -D /dev/tty.usbserial-210 -b 115200` to capture output
```

### Update multiple doc files

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --doc-files docs/getting-started.md docs/setup.md docs/quickstart.md
```

### Create a PR automatically

Requires the [GitHub CLI](https://cli.github.com/) (`gh`):

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --create-pr
```

### Preview changes without modifying anything

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --dry-run --verbose
```

## YAML configuration

Instead of passing all flags on the command line, you can use a config file:

```bash
python -m doc_updater \
  --code-repo ./myapp \
  --docs-repo ./myapp-docs \
  --config config.yaml
```

Example `config.yaml`:

```yaml
docker_image: python:3.11-slim
max_iterations: 3
create_pr: false
verification_instructions: ./verify-instructions.md
```

CLI flags override config file values.

## Safety

The agent has built-in safety boundaries:

- **Write restrictions**: The agent can only write to the docs repo, never the code repo.
- **Sensitive file blocking**: Writes to `.env`, `credentials`, `.ssh`, `.key`, and `.pem` files are blocked.
- **Dangerous command blocking**: Bash commands matching destructive patterns (`rm -rf /`, `sudo rm`, etc.) are denied.
- **Audit logging**: When `--verbose` is enabled, all tool invocations are logged to stderr.
- **Iteration cap**: The update-verify loop stops after `--max-iterations` (default 3) to prevent runaway behavior.

## Project structure

```
src/doc_updater/
  cli.py               # CLI argument parsing
  config.py            # Configuration loading (CLI + YAML)
  orchestrator.py      # Main pipeline: analyze -> update -> verify loop
  agents.py            # Subagent definitions (analyzer, updater, verifier)
  prompts.py           # System prompt templates
  tools.py             # Custom MCP tools (Docker, git)
  hooks.py             # Safety hooks
  permissions.py       # Write permission boundaries
  models.py            # Data contracts between phases
  output.py            # Terminal formatting
```
