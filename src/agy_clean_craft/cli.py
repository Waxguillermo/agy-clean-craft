"""CLI to install and check global Antigravity rules and skills across machines."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = Path.home() / ".gemini" / "config"


def sync_customizations(target_dir: Path, source_root: Path = REPO_ROOT) -> list[Path]:
    """Copy AGENTS.md and skills into the target Antigravity config directory."""
    installed: list[Path] = []

    rules_src = source_root / "rules" / "AGENTS.md"
    rules_dir = target_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    root_rule = target_dir / "AGENTS.md"
    shutil.copy2(rules_src, root_rule)
    installed.append(root_rule)

    nested_rule = rules_dir / "AGENTS.md"
    if nested_rule.exists() or nested_rule.is_symlink():
        nested_rule.unlink()
    nested_rule.symlink_to("../AGENTS.md")
    installed.append(nested_rule)

    skills_src = source_root / "skills"
    for skill_file in sorted(skills_src.glob("*/SKILL.md")):
        skill_name = skill_file.parent.name
        dest_file = target_dir / "skills" / skill_name / "SKILL.md"
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_file, dest_file)
        installed.append(dest_file)

    return installed


def check_status(target_dir: Path, source_root: Path = REPO_ROOT) -> dict[str, bool]:
    """Return installation status for each rule and skill in target_dir."""
    status: dict[str, bool] = {
        "rules/AGENTS.md": (target_dir / "AGENTS.md").is_file(),
    }
    for skill_file in sorted((source_root / "skills").glob("*/SKILL.md")):
        rel = f"skills/{skill_file.parent.name}/SKILL.md"
        status[rel] = (target_dir / rel).is_file()
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agy-sync",
        description="Sync global Antigravity rules and skills to ~/.gemini/config.",
    )
    parser.add_argument(
        "action",
        choices=["install", "status"],
        nargs="?",
        default="install",
        help="Action to run (default: install).",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Target config directory (default: ~/.gemini/config).",
    )
    args = parser.parse_args(argv)

    if args.action == "status":
        status = check_status(args.target)
        for item, ok in status.items():
            mark = "OK" if ok else "MISSING"
            print(f"[{mark}] {args.target / item}")
        return 0 if all(status.values()) else 1

    installed = sync_customizations(args.target)
    print(f"Synced {len(installed)} files to {args.target}:")
    for path in installed:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
