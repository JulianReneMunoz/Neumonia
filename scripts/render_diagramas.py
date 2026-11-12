"""Exporta los diagramas Mermaid (docs/arquitectura/diagramas/*.mmd) a SVG con mermaid-cli.

Uso:  uv run python scripts/render_diagramas.py      (o `make diagramas`; requiere Node.js/npx)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DIAGRAMS = Path(__file__).resolve().parents[1] / "docs" / "arquitectura" / "diagramas"


def main() -> int:
    npx = shutil.which("npx")
    if npx is None:
        print("✗ Se necesita Node.js (npx). Windows: winget install OpenJS.NodeJS.LTS")
        return 1
    sources = sorted(DIAGRAMS.glob("*.mmd"))
    for src in sources:
        out = src.with_suffix(".svg")
        cmd = [
            npx,
            "-y",
            "@mermaid-js/mermaid-cli",
            "-q",
            "-i",
            str(src),
            "-o",
            str(out),
            "-b",
            "white",
        ]
        subprocess.run(cmd, check=True)
        print(f"✓ {out.name}")
    print(f"✓ {len(sources)} diagramas exportados en {DIAGRAMS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
