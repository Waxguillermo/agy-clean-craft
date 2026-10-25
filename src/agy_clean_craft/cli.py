"""CLI to install, check, audit, and uninstall Antigravity rules and skills across machines."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from agy_clean_craft.audit import audit_repository

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = Path.home() / ".gemini" / "config"
BEGIN_MARKER = "<!-- BEGIN agy-clean-craft -->"
END_MARKER = "<!-- END agy-clean-craft -->"


def _merge_managed_block(existing_text: str, managed_content: str) -> str:
    """Insert or update the agy-clean-craft rule block without overwriting user rules."""
    clean_managed = managed_content.strip()
    block = f"{BEGIN_MARKER}\n{clean_managed}\n{END_MARKER}\n"

    if not existing_text.strip() or existing_text.strip() == clean_managed:
        return block

    if BEGIN_MARKER in existing_text and END_MARKER in existing_text:
        before, _, remainder = existing_text.partition(BEGIN_MARKER)
        _, _, after = remainder.partition(END_MARKER)
        prefix = before.rstrip()
        suffix = after.lstrip()
        parts = [p for p in (prefix, block.strip(), suffix) if p]
        return "\n\n".join(parts) + "\n"

    return existing_text.rstrip() + "\n\n" + block


def _remove_managed_block(existing_text: str) -> str:
    """Remove the agy-clean-craft rule block while keeping any other user rules."""
    if BEGIN_MARKER not in existing_text or END_MARKER not in existing_text:
        return existing_text
    before, _, remainder = existing_text.partition(BEGIN_MARKER)
    _, _, after = remainder.partition(END_MARKER)
    parts = [p for p in (before.strip(), after.strip()) if p]
    return ("\n\n".join(parts) + "\n") if parts else ""


def sync_customizations(target_dir: Path, source_root: Path = REPO_ROOT) -> list[Path]:
    """Merge AGENTS.md and copy skill bundles into the target Antigravity config directory."""
    installed: list[Path] = []

    rules_src = source_root / "rules" / "AGENTS.md"
    rules_dir = target_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    root_rule = target_dir / "AGENTS.md"
    existing_text = root_rule.read_text(encoding="utf-8") if root_rule.is_file() else ""
    merged_text = _merge_managed_block(
        existing_text, rules_src.read_text(encoding="utf-8")
    )
    root_rule.write_text(merged_text, encoding="utf-8")
    installed.append(root_rule)

    nested_rule = rules_dir / "AGENTS.md"
    if nested_rule.exists() or nested_rule.is_symlink():
        nested_rule.unlink()
    nested_rule.symlink_to("../AGENTS.md")
    installed.append(nested_rule)

    skills_src = source_root / "skills"
    for skill_file in sorted(skills_src.glob("*/SKILL.md")):
        skill_dir = skill_file.parent
        dest_dir = target_dir / "skills" / skill_dir.name
        shutil.copytree(
            skill_dir,
            dest_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        installed.append(dest_dir / "SKILL.md")

    return installed


def uninstall_customizations(
    target_dir: Path, source_root: Path = REPO_ROOT
) -> list[Path]:
    """Remove agy-clean-craft rules and skills from target_dir while preserving user rules."""
    removed: list[Path] = []

    root_rule = target_dir / "AGENTS.md"
    nested_rule = target_dir / "rules" / "AGENTS.md"
    if root_rule.is_file():
        remaining = _remove_managed_block(root_rule.read_text(encoding="utf-8"))
        if remaining:
            root_rule.write_text(remaining, encoding="utf-8")
        else:
            root_rule.unlink()
            if nested_rule.is_symlink():
                nested_rule.unlink()
        removed.append(root_rule)

    skills_src = source_root / "skills"
    for skill_file in sorted(skills_src.glob("*/SKILL.md")):
        dest_dir = target_dir / "skills" / skill_file.parent.name
        if dest_dir.is_dir():
            shutil.rmtree(dest_dir)
            removed.append(dest_dir)

    return removed


def check_status(target_dir: Path, source_root: Path = REPO_ROOT) -> dict[str, bool]:
    """Return installation status for each rule and skill in target_dir."""
    root_rule = target_dir / "AGENTS.md"
    rule_ok = False
    if root_rule.is_file():
        content = root_rule.read_text(encoding="utf-8")
        rule_ok = BEGIN_MARKER in content or "## 1. Python & `uv` Standard" in content

    status: dict[str, bool] = {
        "rules/AGENTS.md": rule_ok,
    }
    for skill_file in sorted((source_root / "skills").glob("*/SKILL.md")):
        rel = f"skills/{skill_file.parent.name}/SKILL.md"
        status[rel] = (target_dir / rel).is_file()
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agy-sync",
        description="Sync global Antigravity rules and skills or audit a repository.",
    )
    parser.add_argument(
        "action",
        choices=["install", "status", "uninstall", "audit"],
        nargs="?",
        default="install",
        help="Action to run (default: install).",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Target config directory for install/status/uninstall (default: ~/.gemini/config).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root to inspect when running 'audit' (default: current directory).",
    )
    args = parser.parse_args(argv)

    if args.action == "audit":
        findings = audit_repository(args.repo)
        if not findings:
            print(
                f"[LGTM] {args.repo}: zero throwaway scripts, AST slop, or README issues."
            )
            return 0
        print(f"[FAIL] {len(findings)} issue(s) found in {args.repo}:")
        for item in findings:
            print(f"  - {item}")
        return 1

    if args.action == "status":
        status = check_status(args.target)
        for item, ok in status.items():
            mark = "OK" if ok else "MISSING"
            print(f"[{mark}] {args.target / item}")
        return 0 if all(status.values()) else 1

    if args.action == "uninstall":
        removed = uninstall_customizations(args.target)
        print(f"Removed {len(removed)} agy-clean-craft entries from {args.target}.")
        return 0

    installed = sync_customizations(args.target)
    print(f"Synced {len(installed)} files to {args.target}:")
    for path in installed:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
