"""Frontend desacoplado (spec 012): CORS, carga del modelo al arrancar y contrato del cliente."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from neumonia.api.app import create_app, warm_up
from neumonia.config import Settings
from neumonia.controller.service import PneumoniaService
from neumonia.model.classifier import ModelNotFoundError
from tests.conftest import FakeClassifier, FakeExplainer

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_cors_allows_the_frontend_origin_and_exposes_latency(settings):
    # Arrange
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    client = TestClient(create_app(lambda: service, settings))
    # Act
    preflight = client.options(
        "/predict",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    health = client.get("/health", headers={"Origin": "http://localhost:5173"})
    # Assert
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert health.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "X-Process-Time-ms" in health.headers["access-control-expose-headers"]


def test_cors_rejects_unknown_origins(settings):
    # Arrange
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    client = TestClient(create_app(lambda: service, settings))
    # Act
    response = client.get("/health", headers={"Origin": "http://sitio-ajeno.example"})
    # Assert
    assert "access-control-allow-origin" not in response.headers


def test_cors_origins_come_from_the_environment(monkeypatch):
    # Arrange
    monkeypatch.setenv("NEUMONIA_CORS_ORIGINS", "http://localhost:3000/, http://demo.local ")
    # Act
    settings = Settings.from_env()
    # Assert
    assert settings.cors_origins == ("http://localhost:3000", "http://demo.local")


def test_model_is_loaded_once_at_startup(settings):
    # Arrange: el servicio se construye en el arranque, no en la primera petición
    calls = []

    def factory() -> PneumoniaService:
        calls.append(1)
        return PneumoniaService(FakeClassifier(), FakeExplainer())

    # Act
    with TestClient(create_app(factory, settings)) as client:
        before_any_request = len(calls)
        client.get("/health")
        client.get("/health")
    # Assert
    assert before_any_request == 1
    assert len(calls) == 1


def test_api_starts_even_if_the_model_is_missing(settings):
    # Arrange
    def missing() -> PneumoniaService:
        raise ModelNotFoundError("No existe conv_MLP_84.h5")

    # Act
    with TestClient(create_app(missing, settings)) as client:
        body = client.get("/health").json()
    # Assert
    assert body["status"] == "ok"
    assert body["model_loaded"] is False
    assert warm_up(missing) is False


@pytest.mark.parametrize("name", ["index.html", "app.js", "styles.css", "config.js"])
def test_frontend_files_exist(name):
    assert (FRONTEND / name).is_file()


def test_frontend_is_a_separate_client_of_the_api():
    # Arrange
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    # Assert: consume la API por HTTP, modela los 4 estados y no usa Streamlit
    assert "/predict" in js
    assert "/health" in js
    assert "fetch(" in js
    for state in ("idle", "loading", "success", "error"):
        assert f'data-state="{state}"' in html
    assert "streamlit" not in (html + js).lower()
    assert "innerHTML" not in js  # los metadatos se pintan con textContent


def test_frontend_has_report_and_3d_tabs():
    # Arrange
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    # Assert: informe y vista 3D salen de `findings` de la API, sin librerías externas
    for tab in ("res", "inf", "3d"):
        assert f'data-tab="{tab}"' in html
        assert f'data-panel="{tab}"' in html
    assert '<canvas id="v3d"' in html
    assert "findings.attention_grid" in js
    assert "shortcut_warning" in js
    assert '<script src="http' not in html  # sin CDN: funciona sin internet


def test_frontend_3d_tab_shows_the_ct_reconstruction():
    # Arrange
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    # Assert: SPEC-018, pulmones y lesión desde la API; Plotly.js servido por la propia API
    assert 'id="ct-plot"' in html
    assert 'data-v3d="ct"' in html
    assert 'data-v3d="att"' in html
    assert "/ct/cases" in js
    assert "/vendor/plotly.min.js" in js
    for name in ("pulmon_derecho", "vidrio_esmerilado", "consolidacion", "via_aerea", "vasos"):
        assert name in js
    assert "cdn.plot.ly" not in js
