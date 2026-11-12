"""La vista Streamlit se renderiza sin cargar el modelo (carga perezosa) — AppTest oficial."""

from __future__ import annotations

import pytest

from tests.conftest import ROOT

APP = ROOT / "src" / "neumonia" / "view" / "streamlit_app.py"


@pytest.fixture
def app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(APP), default_timeout=30).run()


def test_app_renders_without_errors(app):
    assert not app.exception
    assert "neumonía" in app.title[0].value.lower()


def test_predict_button_disabled_until_upload(app):
    assert app.sidebar.button[0].disabled


def test_disclaimer_is_visible(app):
    assert any("no reemplaza" in w.value.lower() for w in app.warning)
