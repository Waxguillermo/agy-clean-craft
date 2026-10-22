# Global Engineering & Workflow Rules

## 1. Python & `uv` Standard
- Always use **`uv`** for Python environment, dependency, and script management:
  - Run scripts/tools: `uv run <cmd>` (or `uvx <tool>` for standalone CLI tools like `uvx ruff`).
  - Add dependencies: `uv add <pkg>` / `uv add --dev <pkg>`.
  - Sync environment: `uv sync`.
- Never use bare `pip install` or global `python` when working in a project.

## 2. Zero Slop & No Throwaway `.py` Scripts
- **NEVER create ad-hoc or throwaway `.py` scripts** in the project directory (e.g., `test_quick.py`, `debug.py`, `tmp.py`, `check_*.py`, `verify_*.py`) to test or inspect behavior.
- For quick verification:
  - Use one-liners: `uv run python -c "..."`
  - Or run the real test suite: `uv run pytest`
  - If a temporary multi-line script is strictly necessary, write it to `/tmp/` or the session `scratch/` directory and delete it immediately after use.
- **Anti-Slop Code Quality**:
  - Write minimal, idiomatic code that solves only the requested problem.
  - Do not introduce speculative abstractions, unused parameters, dead code, or redundant comments that merely restate the code.
  - Do not wrap code in broad `try/except Exception:` blocks that silently swallow errors.

## 3. README Philosophy (3 Pillars + Visuals)
Whenever creating or updating a `README.md`, activate the **`readme-craft`** skill and enforce three pillars:
1. **Understandability**: Explain what the project does and how it works at a glance, using **visuals whenever helpful** (Mermaid architecture/flow diagrams, data visualizations/charts, or UI screenshots).
2. **Easy Deployment**: Provide zero-friction, copy-pasteable `uv` setup and deployment commands (`uv sync`, `uv run ...`, environment variables).
3. **Utility for Newcomers**: Give newcomers a clear mental map (key entrypoints, minimal working example, and how to run tests/checks) without verbose walls of text.

## 4. Clean Git & Pre-Push Discipline
- Before running `git commit` or `git push`, always follow the **`clean-ship`** skill workflow:
  1. Verify `git status --short` has no untracked throwaway scripts, debug logs, or artifacts.
  2. Format and lint with `uv` (`uvx ruff check --fix . && uvx ruff format .`) and run tests (`uv run pytest`).
  3. Spawn a dedicated **Janitor / Reviewer Subagent** to audit the diff for code slop and README quality before pushing.
  4. Stage files explicitly (`git add <specific-files>`) rather than blind `git add .`.
