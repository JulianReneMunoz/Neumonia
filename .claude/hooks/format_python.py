"""Hook PostToolUse: formatea con Ruff cada archivo .py que el agente edita.

Claude Code envía por stdin un JSON con `tool_input.file_path`. Nunca bloquea: si Ruff falla,
solo informa por stderr (código 0) para no interrumpir al agente.
"""

from __future__ import annotations

import json
import subprocess
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    path = (payload.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".py"):
        return 0
    for args in (["ruff", "format", path], ["ruff", "check", "--fix", "--quiet", path]):
        result = subprocess.run(["uv", "run", *args], capture_output=True, text=True, check=False)  # noqa: S603, S607
        if result.returncode != 0:
            print(result.stdout + result.stderr, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
