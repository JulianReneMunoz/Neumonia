"""SPEC-018: la API expone los casos de tomografía ya procesados al frontend desacoplado."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from fastapi.testclient import TestClient

from neumonia.api.app import create_app
from neumonia.api.ct_routes import plotly_js_path
from neumonia.controller.service import PneumoniaService
from neumonia.model.ct_cache import save_case
from neumonia.model.ct_mesh import Mesh
from tests.conftest import FakeClassifier, FakeExplainer


def _client(settings, tmp_path):
    cache = tmp_path / "ct_cache"
    tetra = Mesh(
        np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0], [0, 0, 10]], dtype=np.float32),
        np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.int32),
    )
    empty = Mesh(np.zeros((0, 3), np.float32), np.zeros((0, 3), np.int32))
    report = {
        "case_id": "caso_demo",
        "lung_volume_ml": {"derecho": 100.0, "izquierdo": 90.0},
        "lesion_ml": 12.0,
        "ggo_ml": 10.0,
        "consolidation_ml": 2.0,
        "percent_total": 3.5,
        "percent_by_lung": {"derecho": 5.0, "izquierdo": 2.0},
        "lobes": [],
        "severity_score": 2,
        "summary": ["Compromiso leve."],
    }
    save_case(
        cache / "caso_demo.npz",
        "caso_demo",
        {"pulmon_derecho": tetra, "vidrio_esmerilado": tetra, "via_aerea": empty},
        report,
        np.zeros((4, 4, 4), np.uint8),
        (1.0, 1.0, 1.0),
    )
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    return TestClient(create_app(lambda: service, replace(settings, ct_cache_dir=cache)))


def test_lists_the_processed_ct_cases(settings, tmp_path):
    # Act
    body = _client(settings, tmp_path).get("/ct/cases").json()
    # Assert
    assert body == {"cases": ["caso_demo"]}


def test_returns_meshes_and_report_of_a_case(settings, tmp_path):
    # Act
    response = _client(settings, tmp_path).get("/ct/cases/caso_demo")
    body = response.json()
    # Assert
    assert response.status_code == 200
    assert set(body["structures"]) == {"pulmon_derecho", "vidrio_esmerilado"}  # sin mallas vacías
    assert len(body["structures"]["pulmon_derecho"]["vertices"]) == 4
    assert body["structures"]["pulmon_derecho"]["faces"][0] == [0, 1, 2]
    assert body["report"]["severity_score"] == 2
    assert "lobulo_medio_derecho" in body["lobe_labels"]


def test_unknown_case_is_404_and_paths_are_not_accepted(settings, tmp_path):
    # Arrange
    client = _client(settings, tmp_path)
    # Act / Assert
    assert client.get("/ct/cases/no_existe").status_code == 404
    assert client.get("/ct/cases/..%2F..%2Fsecreto").status_code == 404


def test_serves_plotly_js_from_the_installed_package(settings, tmp_path):
    # Act
    response = _client(settings, tmp_path).get("/vendor/plotly.min.js")
    # Assert
    assert plotly_js_path().is_file()
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
