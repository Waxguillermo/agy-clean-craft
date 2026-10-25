from pathlib import Path

from agy_clean_craft.cli import (
    BEGIN_MARKER,
    END_MARKER,
    check_status,
    main,
    sync_customizations,
    uninstall_customizations,
)


def test_sync_and_status(tmp_path: Path) -> None:
    status_before = check_status(tmp_path)
    assert not any(status_before.values())

    installed = sync_customizations(tmp_path)
    assert len(installed) == 4
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "rules" / "AGENTS.md").is_symlink()
    assert (tmp_path / "skills" / "readme-craft" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "clean-ship" / "SKILL.md").is_file()

    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert BEGIN_MARKER in content
    assert END_MARKER in content

    status_after = check_status(tmp_path)
    assert all(status_after.values())


def test_sync_preserves_existing_user_rules_and_is_idempotent(tmp_path: Path) -> None:
    user_rule = "# My Custom Rules\n- Always use strict typing.\n"
    root_rule = tmp_path / "AGENTS.md"
    root_rule.write_text(user_rule, encoding="utf-8")

    sync_customizations(tmp_path)
    first_pass = root_rule.read_text(encoding="utf-8")
    assert "# My Custom Rules" in first_pass
    assert BEGIN_MARKER in first_pass
    assert first_pass.count(BEGIN_MARKER) == 1

    # Running sync a second time updates in-place without duplicating the block
    sync_customizations(tmp_path)
    second_pass = root_rule.read_text(encoding="utf-8")
    assert second_pass == first_pass
    assert second_pass.count(BEGIN_MARKER) == 1

    # Uninstall removes only the agy-clean-craft block and preserves user rules
    uninstall_customizations(tmp_path)
    after_uninstall = root_rule.read_text(encoding="utf-8")
    assert "# My Custom Rules" in after_uninstall
    assert BEGIN_MARKER not in after_uninstall
    assert not (tmp_path / "skills" / "clean-ship").exists()


def test_cli_entrypoints(tmp_path: Path) -> None:
    assert main(["status", "--target", str(tmp_path)]) == 1
    assert main(["install", "--target", str(tmp_path)]) == 0
    assert main(["status", "--target", str(tmp_path)]) == 0
    assert main(["uninstall", "--target", str(tmp_path)]) == 0
    assert main(["status", "--target", str(tmp_path)]) == 1
