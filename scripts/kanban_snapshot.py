"""Copia versionada del tablero Kanban (SPEC-019): regenera docs/kanban.md desde GitHub Projects.

Uso:
  make kanban
  uv run python scripts/kanban_snapshot.py [--owner OWNER] [--project 5] [--out docs/kanban.md]

Requisito: `gh` autenticado con el scope `project` (`gh auth refresh -s project`).
No usa dependencias nuevas: llama a `gh project item-list` mediante subprocess.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "JulianReneMunoz"
PROJECT = 5
COLUMNAS = ("Backlog", "Todo", "In Progress", "En revisión", "Done")
WIP_LIMIT = 3
SIN_ESTADO = "Sin estado"

POLITICA = {
    "Backlog": "Ideas e historias registradas que aún no se priorizan para el módulo en curso.",
    "Todo": "Historias priorizadas, con criterios de aceptación, listas para empezar.",
    "In Progress": (
        f"Trabajo en desarrollo en una rama `feature/*` o `fix/*`. Límite WIP: **{WIP_LIMIT}**."
    ),
    "En revisión": "PR abierto hacia `develop`, a la espera de CI en verde y revisión.",
    "Done": (
        "PR fusionado con CI en verde (lint, pruebas en Ubuntu y Windows, Docker) o issue cerrado."
    ),
}


def fetch_items(owner: str, project: int) -> list[dict]:
    """Devuelve los ítems del tablero tal como los entrega `gh project item-list`."""
    out = subprocess.run(
        [
            "gh",
            "project",
            "item-list",
            str(project),
            "--owner",
            owner,
            "--limit",
            "500",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return json.loads(out)["items"]


def normalize(items: list[dict]) -> list[dict]:
    """Reduce cada ítem a número, título, tipo, etiquetas, enlace y columna."""
    filas = []
    for item in items:
        content = item.get("content") or {}
        tipo = {"Issue": "Issue", "PullRequest": "PR"}.get(content.get("type"), "Borrador")
        filas.append(
            {
                "numero": content.get("number"),
                "titulo": (content.get("title") or item.get("title") or "").replace("|", "\\|"),
                "tipo": tipo,
                "etiquetas": sorted(item.get("labels") or []),
                "url": content.get("url", ""),
                "estado": item.get("status") or SIN_ESTADO,
            }
        )
    return sorted(filas, key=lambda f: (f["numero"] is None, -(f["numero"] or 0)))


def count_by_column(filas: list[dict]) -> dict[str, int]:
    """Conteo por columna en el orden del tablero (incluye columnas vacías)."""
    extras = sorted({f["estado"] for f in filas} - set(COLUMNAS))
    return {col: sum(f["estado"] == col for f in filas) for col in (*COLUMNAS, *extras)}


def render(filas: list[dict], corte: date, owner: str = OWNER, project: int = PROJECT) -> str:
    """Genera el Markdown de docs/kanban.md."""
    url = f"https://github.com/users/{owner}/projects/{project}"
    conteo = count_by_column(filas)
    lineas = [
        "# Tablero Kanban del proyecto",
        "",
        f"> Copia versionada del tablero **[Neumonía · Kanban]({url})**"
        f" (GitHub Projects #{project}).",
        f"> Fecha de corte: **{corte.isoformat()}** · Se regenera con `make kanban` (SPEC-019).",
        "",
        "## Política Kanban",
        "",
        "| Columna | Definición |",
        "|---|---|",
        *(f"| **{col}** | {POLITICA[col]} |" for col in COLUMNAS),
        "",
        f"- **Límite WIP:** como máximo {WIP_LIMIT} ítems en *In Progress*; si se alcanza,"
        " se termina o se revisa antes de empezar algo nuevo.",
        "- **Criterio de Done:** PR fusionado en `develop` con CI en verde;"
        " el issue asociado se cierra con `Closes #n`.",
        "- **Flujo:** una historia (issue) por funcionalidad → rama `feature/*`"
        " → PR a `develop` → Done.",
        "",
        "## Conteo por columna",
        "",
        "| Columna | Ítems |",
        "|---|:-:|",
        *(f"| {col} | {n} |" for col, n in conteo.items()),
        f"| **Total** | **{len(filas)}** |",
        "",
    ]
    if conteo.get("In Progress", 0) > WIP_LIMIT:
        lineas += [f"> ⚠️ *In Progress* supera el límite WIP de {WIP_LIMIT}.", ""]
    for col in conteo:
        lineas += [f"## {col}", ""]
        de_col = [f for f in filas if f["estado"] == col]
        if not de_col:
            lineas += ["_Sin ítems._", ""]
            continue
        lineas += ["| # | Título | Tipo | Etiquetas | Enlace |", "|:-:|---|:-:|---|---|"]
        for f in de_col:
            etiquetas = " ".join(f"`{e}`" for e in f["etiquetas"]) or "—"
            enlace = f"[abrir]({f['url']})" if f["url"] else "—"
            lineas.append(
                f"| {f['numero'] or '—'} | {f['titulo']} | {f['tipo']} | {etiquetas} | {enlace} |"
            )
        lineas.append("")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", default=OWNER)
    parser.add_argument("--project", type=int, default=PROJECT)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "kanban.md")
    args = parser.parse_args(argv)
    filas = normalize(fetch_items(args.owner, args.project))
    args.out.write_text(render(filas, date.today(), args.owner, args.project), encoding="utf-8")
    conteo = ", ".join(f"{c}: {n}" for c, n in count_by_column(filas).items())
    print(f"{args.out} actualizado · {len(filas)} ítems · {conteo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
