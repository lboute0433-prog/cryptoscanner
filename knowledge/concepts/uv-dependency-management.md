---
title: "uv Dependency Management"
aliases: [uv, python-deps, uv-sync]
tags: [tooling, python, dependencies, setup]
sources:
  - "daily/test-setup.md"
created: 2026-04-23
updated: 2026-04-23
---

# uv Dependency Management

`uv` is the Python package and project manager used to install and run dependencies for the memory compiler system. It replaces `pip`/`venv`/`poetry` with a single fast tool that resolves, locks, and installs packages from `pyproject.toml`.

## Key Points

- `uv sync` installs all dependencies declared in `pyproject.toml` into an isolated virtual environment
- All scripts are invoked via `uv run python <script>` to guarantee the correct environment is active
- `pyproject.toml` lives at the project root so hooks and scripts share the same environment
- `uv.lock` is committed to version control to guarantee reproducible installs across machines
- No separate `requirements.txt` — `pyproject.toml` is the single source of truth for dependencies

## Details

The memory compiler depends on `claude-agent-sdk`, `python-dotenv`, and `tzdata` (for timezone-aware scheduling). These are declared in `pyproject.toml` under `[project.dependencies]`. Running `uv sync` after cloning the repository installs all of them into `.venv/` in the project root.

Hook commands in `.claude/settings.json` use the `uv run python hooks/<script>.py` pattern rather than a bare `python` call. This ensures the hook always executes inside the uv-managed virtual environment, regardless of the system Python version or any active conda/pyenv state. The same pattern applies to all CLI scripts (`compile.py`, `query.py`, `lint.py`).

The `uv.lock` lockfile captures exact versions and hashes for all transitive dependencies, enabling bit-for-bit reproducible installs. It is committed to git. The generated state files (`scripts/state.json`, `scripts/last-flush.json`) and the `.venv/` directory are excluded from version control since they are machine-specific runtime artifacts.

## Related Concepts

- [[concepts/memory-compiler-architecture]] — compile.py and flush.py are invoked via `uv run`
- [[concepts/hook-system]] — all hook commands use the `uv run python hooks/<script>.py` pattern

## Sources

- [[daily/test-setup.md]] — `uv sync` executed during initial setup to install project dependencies
