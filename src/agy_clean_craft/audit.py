"""Repository and README hygiene auditor for agy-clean-craft."""

from __future__ import annotations

import ast
import re
from pathlib import Path

THROWAWAY_PATTERNS = (
    re.compile(r"^(debug|tmp|test_quick|verify|check_|dump_|scratch).*\.py$"),
    re.compile(r"^.*\.(bak|orig)$"),
)
UNQUOTED_MERMAID_LABEL_RE = re.compile(r"\[[^\"\]\n]*\([^\]\n]*\)[^\"\]\n]*\]")
BARE_PIP_INSTALL_RE = re.compile(r"(?<![\w-])pip3?\s+install\b")
MERMAID_BLOCK_RE = re.compile(r"^```mermaid\s*\n(.*?)^```", re.DOTALL | re.MULTILINE)
FENCED_BLOCK_RE = re.compile(
    r"^```([a-zA-Z0-9_-]*)\s*\n(.*?)^```", re.DOTALL | re.MULTILINE
)


def check_throwaway_files(repo_root: Path) -> list[str]:
    """Flag ad-hoc throwaway scripts or backup files in the repository."""
    findings: list[str] = []
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}

    for path in sorted(repo_root.rglob("*")):
        if any(part in skip_dirs for part in path.parts) or not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(pattern.match(path.name) for pattern in THROWAWAY_PATTERNS):
            findings.append(
                f"Throwaway file detected: '{rel}' (delete or move to /tmp)"
            )
    return findings


def _is_silent_handler(handler: ast.ExceptHandler) -> bool:
    """Return True if an except handler catches Exception/BaseException and only passes."""
    if handler.type is not None and not (
        isinstance(handler.type, ast.Name)
        and handler.type.id in {"Exception", "BaseException"}
    ):
        return False
    if len(handler.body) != 1:
        return False
    stmt = handler.body[0]
    if isinstance(stmt, ast.Pass):
        return True
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)


def check_python_ast_slop(repo_root: Path) -> list[str]:
    """Scan Python files for silent broad try/except blocks."""
    findings: list[str] = []
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}

    for py_file in sorted(repo_root.rglob("*.py")):
        if any(part in skip_dirs for part in py_file.parts):
            continue
        rel = py_file.relative_to(repo_root)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(rel))
        except SyntaxError as exc:
            findings.append(f"Syntax error in '{rel}:{exc.lineno}': {exc.msg}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and _is_silent_handler(node):
                findings.append(
                    f"Silent broad exception handler in '{rel}:{node.lineno}' "
                    "(avoid 'except Exception: pass')"
                )
    return findings


def check_readme_pillars(repo_root: Path) -> list[str]:
    """Validate README.md against the 3-pillar visual and uv standard."""
    readme_path = repo_root / "README.md"
    if not readme_path.is_file():
        return ["Missing 'README.md' at repository root"]

    findings: list[str] = []
    text = readme_path.read_text(encoding="utf-8")

    # 1. Visual check (Mermaid diagram or embedded image)
    has_mermaid = "```mermaid" in text
    has_image = "![" in text
    if not (has_mermaid or has_image):
        findings.append(
            "README.md is missing a visual overview (Mermaid diagram or screenshot/chart)"
        )

    # 2. Mermaid syntax safety (unquoted parentheses inside square-bracket node labels)
    for block in MERMAID_BLOCK_RE.findall(text):
        for match in UNQUOTED_MERMAID_LABEL_RE.findall(block):
            findings.append(
                f"Unquoted parentheses in Mermaid label '{match}' in README.md "
                '(wrap label in double quotes: ["..."])'
            )

    # 3. Bare pip install check inside shell code blocks
    for lang, block in FENCED_BLOCK_RE.findall(text):
        if lang not in {"", "bash", "sh", "shell", "zsh", "console"}:
            continue
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "uv pip install" in stripped:
                continue
            if BARE_PIP_INSTALL_RE.search(stripped):
                findings.append(
                    f"Bare 'pip install' found in README.md ('{stripped}'); use 'uv' instead"
                )

    # 4. Verify file paths listed in Newcomer Map table exist on disk
    if "## Newcomer Map" in text:
        _, _, after = text.partition("## Newcomer Map")
        section = after.split("\n## ", maxsplit=1)[0]
        for line in section.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells:
                continue
            first_cell = cells[0]
            code_match = re.match(r"^`([^`]+)`$", first_cell)
            if not code_match:
                continue
            candidate = code_match.group(1)
            is_path = "/" in candidate or candidate.endswith(
                (".py", ".md", ".json", ".toml", ".svg")
            )
            if (
                is_path
                and "<" not in candidate
                and not (repo_root / candidate).exists()
            ):
                findings.append(
                    f"Broken path in README.md Newcomer Map: '{candidate}' does not exist"
                )

    return findings


def audit_repository(repo_root: Path) -> list[str]:
    """Run all workspace, AST, and README hygiene checks on repo_root."""
    return [
        *check_throwaway_files(repo_root),
        *check_python_ast_slop(repo_root),
        *check_readme_pillars(repo_root),
    ]
