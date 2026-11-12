"""Hook PreToolUse: bloquea comandos que violan las reglas del curso.

Código de salida 2 = bloquear y devolver el motivo al agente (protocolo de hooks de Claude Code).
"""

from __future__ import annotations

import json
import re
import sys

RULES: list[tuple[str, str]] = [
    (r"\bpip3?\s+install\b", "Prohibido pip en este curso: use `uv add <paquete>`."),
    (
        r"requirements\.txt",
        "No se usa requirements.txt: las dependencias viven en pyproject.toml + uv.lock.",
    ),
    (
        r"git\s+add\s+.*\.(h5|keras|onnx|pt|pkl)\b",
        "Los pesos no se versionan (ver .gitignore y make model).",
    ),
    (r"git\s+add\s+.*(\.env\b|kaggle\.json)", "No versione secretos."),
    (r"git\s+push\s+.*(--force|-f\b)", "Push forzado prohibido; abra un PR."),
    (
        r"git\s+push\s+\S+\s+(main|develop)\b",
        "No se hace push directo a main/develop: use PR (Gitflow).",
    ),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    for pattern, reason in RULES:
        if re.search(pattern, command):
            print(reason, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
