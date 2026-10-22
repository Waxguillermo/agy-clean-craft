---
name: clean-ship
description: >-
  Mandatory pre-commit and pre-push hygiene workflow. Activate whenever finishing
  a coding task, committing changes, or pushing to git to eliminate throwaway .py
  scripts, code slop, lint errors, and outdated or verbose READMEs.
---

# Clean & Ship Workflow

Follow this exact method every time before committing or pushing code.

## Step 1: Workspace Sweep (Eliminate Throwaway Scripts)
1. Run `git status --short` and `git status --ignored --short`.
2. Delete any untracked ad-hoc scripts (`debug*.py`, `tmp*.py`, `test_quick*.py`, `verify*.py`, `scratch*.py`), temporary JSON/CSV dumps, or log files that do not belong in the repository.
3. Verify `.gitignore` covers `.venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`, and `.env`.

## Step 2: Format, Lint & Test with `uv`
1. Format and lint Python files:
   ```bash
   uvx ruff check --fix . && uvx ruff format .
   ```
2. If tests exist, run them via `uv`:
   ```bash
   uv run pytest
   ```
3. Fix any failing tests or lint issues before continuing.

## Step 3: README & Visual Check
1. If entrypoints, architecture, CLI flags, or deployment steps changed, activate the **`readme-craft`** skill and update `README.md`.
2. Verify the README remains concise and satisfies the 3 pillars (**Understandability**, **Easy Deployment** with `uv`, **Utility for Newcomers**) and includes a **Mermaid diagram, dataviz, or screenshot** when helpful.

## Step 4: Independent Subagent Audit (`code-janitor`)
For any non-trivial change, spawn an independent review subagent using `define_subagent` and `invoke_subagent`:
- **Name**: `code-janitor`
- **SystemPrompt**:
  > You are a strict Code & Documentation Janitor. Inspect `git status` and `git diff`. Flag: (1) any untracked or throwaway `.py` scripts, (2) AI code slop (dead code, unused helpers, silent try/except blocks, redundant comments), (3) raw `pip`/`python` commands instead of `uv`, and (4) verbose or unclear README sections. Return a short bulleted list of required fixes, or `LGTM` if clean.
- Fix every issue reported by `code-janitor` before committing.

## Step 5: Explicit Stage, Commit & Push
1. Stage only intentional files explicitly:
   ```bash
   git add <file1> <file2>
   ```
   *(Never run `git add .` or `git add -A` blindly.)*
2. Verify staged changes with `git diff --staged --stat`.
3. Commit with a concise `type: summary` message (e.g., `feat: add uv pipeline runner`) and push.
