"""Antigravity PreToolUse lifecycle hook handlers for agy-clean-craft."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from agy_clean_craft.audit import BARE_PIP_INSTALL_RE, THROWAWAY_PATTERNS

BLIND_GIT_ADD_RE = re.compile(r"(?:^|[;&|]\s*)git\s+add\s+(?:\.|-A|--all)(?:\s|$)")
ALLOWED_TEMP_PARTS = {"tmp", "scratch", "var", "folders"}


def evaluate_pre_tool_use(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a PreToolUse event payload and return an allow/deny decision."""
    tool_call = payload.get("toolCall") or {}
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args") or {}

    if tool_name == "write_file":
        raw_path = str(args.get("Path", ""))
        if raw_path:
            path = Path(raw_path)
            in_temp = any(part in ALLOWED_TEMP_PARTS for part in path.parts)
            is_throwaway = any(
                pattern.match(path.name) for pattern in THROWAWAY_PATTERNS
            )
            if not in_temp and is_throwaway:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Blocked by agy-clean-craft: Do not create throwaway script "
                        f"'{path.name}' in the project. Use 'uv run python -c ...', "
                        "'uv run pytest', or write temporary files to /tmp."
                    ),
                }

    if tool_name == "run_command":
        cmd = str(args.get("CommandLine", ""))
        if "uv pip install" not in cmd and BARE_PIP_INSTALL_RE.search(cmd):
            return {
                "decision": "deny",
                "reason": (
                    "Blocked by agy-clean-craft: Never use bare 'pip install'. "
                    "Use 'uv add <pkg>', 'uv sync', or 'uv run' instead."
                ),
            }
        if BLIND_GIT_ADD_RE.search(cmd):
            return {
                "decision": "deny",
                "reason": (
                    "Blocked by agy-clean-craft: Stage files explicitly "
                    "('git add <file1> <file2>') instead of blind 'git add .'."
                ),
            }

    return {"decision": "allow"}


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow"}))
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
        return 0

    result = evaluate_pre_tool_use(payload)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
