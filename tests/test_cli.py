from pathlib import Path

from agy_clean_craft.audit import audit_repository
from agy_clean_craft.cli import (
    BEGIN_MARKER,
    END_MARKER,
    REPO_ROOT,
    check_status,
    main,
    sync_customizations,
    uninstall_customizations,
)
from agy_clean_craft.hooks import evaluate_pre_tool_use


def test_sync_and_status(tmp_path: Path) -> None:
    status_before = check_status(tmp_path)
    assert not any(status_before.values())

    installed = sync_customizations(tmp_path)
    assert len(installed) == 4
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "rules" / "AGENTS.md").is_symlink()
    assert (tmp_path / "skills" / "readme-craft" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "clean-ship" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "clean-ship" / "scripts" / "audit.py").is_file()

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

    sync_customizations(tmp_path)
    second_pass = root_rule.read_text(encoding="utf-8")
    assert second_pass == first_pass
    assert second_pass.count(BEGIN_MARKER) == 1

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
    assert main(["audit", "--repo", str(REPO_ROOT)]) == 0


def test_audit_detects_throwaway_slop_and_readme_issues(tmp_path: Path) -> None:
    (tmp_path / "debug_quick.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "try:\n    1 / 0\nexcept Exception:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Demo\n\n```mermaid\nflowchart LR\n    A[Parser (uv)] --> B[Out]\n```\n\n"
        "```bash\npip install requests\n```\n\n"
        "## Newcomer Map\n\n| Path | Purpose |\n| :--- | :--- |\n| `missing.py` | Gone |\n",
        encoding="utf-8",
    )

    findings = audit_repository(tmp_path)
    assert any("Throwaway file detected: 'debug_quick.py'" in f for f in findings)
    assert any("Silent broad exception handler" in f for f in findings)
    assert any("Unquoted parentheses in Mermaid label" in f for f in findings)
    assert any("Bare 'pip install' found in README.md" in f for f in findings)
    assert any(
        "Broken path in README.md Newcomer Map: 'missing.py'" in f for f in findings
    )


def test_pre_tool_use_hooks() -> None:
    deny_script = evaluate_pre_tool_use(
        {
            "toolCall": {
                "name": "write_file",
                "args": {"Path": "/repo/project/debug_test.py"},
            }
        }
    )
    assert deny_script["decision"] == "deny"

    allow_tmp_script = evaluate_pre_tool_use(
        {"toolCall": {"name": "write_file", "args": {"Path": "/tmp/debug_test.py"}}}
    )
    assert allow_tmp_script["decision"] == "allow"

    deny_pip = evaluate_pre_tool_use(
        {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "pip install pytest"},
            }
        }
    )
    assert deny_pip["decision"] == "deny"

    deny_git_add = evaluate_pre_tool_use(
        {"toolCall": {"name": "run_command", "args": {"CommandLine": "git add ."}}}
    )
    assert deny_git_add["decision"] == "deny"

    allow_uv = evaluate_pre_tool_use(
        {"toolCall": {"name": "run_command", "args": {"CommandLine": "uv run pytest"}}}
    )
    assert allow_uv["decision"] == "allow"
