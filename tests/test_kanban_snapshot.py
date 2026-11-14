"""SPEC-019: la copia versionada del Kanban se genera con datos de `gh` (dobles en memoria)."""

from __future__ import annotations

import importlib.util
from datetime import date

import pytest

from tests.conftest import ROOT


@pytest.fixture(scope="module")
def kanban():
    spec = importlib.util.spec_from_file_location(
        "kanban_snapshot", ROOT / "scripts" / "kanban_snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _item(number, kind, status, labels=(), title="Título"):
    return {
        "content": {
            "number": number,
            "title": title,
            "type": kind,
            "url": f"https://github.com/o/r/{'pull' if kind == 'PullRequest' else 'issues'}/"
            f"{number}",
        },
        "labels": list(labels),
        "status": status,
    }


def test_normalize_maps_type_labels_and_sorts_by_number(kanban):
    # Arrange
    items = [_item(3, "Issue", "Todo", ["qa", "docs"]), _item(9, "PullRequest", "Done")]
    # Act
    filas = kanban.normalize(items)
    # Assert
    assert [f["numero"] for f in filas] == [9, 3]
    assert filas[0]["tipo"] == "PR"
    assert filas[1]["etiquetas"] == ["docs", "qa"]


def test_count_by_column_keeps_board_order_and_empty_columns(kanban):
    # Arrange
    filas = kanban.normalize([_item(1, "Issue", "Done"), _item(2, "Issue", None)])
    # Act
    conteo = kanban.count_by_column(filas)
    # Assert
    assert list(conteo)[:5] == list(kanban.COLUMNAS)
    assert conteo["Done"] == 1
    assert conteo["Backlog"] == 0
    assert conteo[kanban.SIN_ESTADO] == 1


def test_render_includes_link_policy_tables_count_and_cutoff(kanban):
    # Arrange
    filas = kanban.normalize(
        [
            _item(31, "PullRequest", "En revisión", ["docs"], "docs | README"),
            _item(5, "Issue", "Done"),
        ]
    )
    # Act
    md = kanban.render(filas, date(2026, 11, 14))
    # Assert
    assert "https://github.com/users/JulianReneMunoz/projects/5" in md
    assert "2026-11-14" in md
    assert "Límite WIP:** como máximo 3" in md
    assert "PR fusionado en `develop` con CI en verde" in md
    assert "| 31 | docs \\| README | PR | `docs` |" in md
    assert "| **Total** | **2** |" in md
    assert "## Backlog\n\n_Sin ítems._" in md


def test_render_warns_when_wip_limit_is_exceeded(kanban):
    # Arrange
    filas = kanban.normalize([_item(n, "Issue", "In Progress") for n in range(1, 5)])
    # Act
    md = kanban.render(filas, date(2026, 11, 14))
    # Assert
    assert "supera el límite WIP de 3" in md
