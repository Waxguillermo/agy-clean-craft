from pathlib import Path

from agy_clean_craft.cli import check_status, main, sync_customizations


def test_sync_and_status(tmp_path: Path) -> None:
    status_before = check_status(tmp_path)
    assert not any(status_before.values())

    installed = sync_customizations(tmp_path)
    assert len(installed) == 4
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "rules" / "AGENTS.md").is_symlink()
    assert (tmp_path / "skills" / "readme-craft" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "clean-ship" / "SKILL.md").is_file()

    status_after = check_status(tmp_path)
    assert all(status_after.values())


def test_cli_entrypoints(tmp_path: Path) -> None:
    assert main(["status", "--target", str(tmp_path)]) == 1
    assert main(["install", "--target", str(tmp_path)]) == 0
    assert main(["status", "--target", str(tmp_path)]) == 0
