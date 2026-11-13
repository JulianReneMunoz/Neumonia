"""Aplicación única: radiografía y tomografía en el mismo puerto (spec 010)."""

from __future__ import annotations

import importlib.util

import pytest

from neumonia.view.app import PAGES, VIEW_DIR

needs_ct = pytest.mark.skipif(
    importlib.util.find_spec("skimage") is None, reason="requiere el extra `ct`"
)


def test_pages_point_to_the_existing_views():
    # Arrange / Act
    scripts = [spec.path for spec in PAGES]
    # Assert
    assert [p.name for p in scripts] == ["streamlit_app.py", "ct_app.py"]
    assert all(p.is_file() for p in scripts)
    assert all(p.parent == VIEW_DIR for p in scripts)


def test_radiography_is_the_only_default_page_and_urls_are_unique():
    defaults = [spec for spec in PAGES if spec.default]
    assert [spec.url_path for spec in defaults] == ["radiografia"]
    assert len({spec.url_path for spec in PAGES}) == len(PAGES)
    assert "prototipo" in PAGES[1].title.lower()


@needs_ct
def test_unified_app_runs_both_pages(tmp_path, monkeypatch):
    # Arrange: sin modelo ni casos de tomografía, las dos páginas deben dibujarse sin errores
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("NEUMONIA_CT_CACHE_DIR", str(tmp_path / "ct_cache"))
    app = AppTest.from_file(str(VIEW_DIR / "app.py"), default_timeout=60)
    # Act
    app.run()
    # Assert: abre en radiografía
    assert not app.exception
    assert "neumon" in app.title[0].value.lower()
    # Act: cambia a la página de tomografía
    app.switch_page(str(VIEW_DIR / "ct_app.py"))
    app.run()
    # Assert
    assert not app.exception
    assert "tomograf" in app.title[0].value.lower()
