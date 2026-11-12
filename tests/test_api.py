"""Contrato REST (tests/README.md del curso): health, predict ok, inválidos y forma del JSON."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from neumonia.api.app import create_app
from neumonia.controller.service import PneumoniaService
from tests.conftest import (
    EXPECTED,
    SAMPLE_FILES,
    ExplodingClassifier,
    FakeClassifier,
    FakeExplainer,
)


@pytest.fixture
def client(settings) -> TestClient:
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    return TestClient(create_app(service_factory=lambda: service, settings=settings))


def test_health(client):
    # Act
    response = client.get("/health")
    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize("path", SAMPLE_FILES, ids=lambda p: p.name)
def test_predict_ok_with_course_samples(client, path):
    response = client.post("/predict", files={"file": (path.name, path.read_bytes())})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] in {"NORMAL", "PNEUMONIA"}
    assert 0.0 <= body["probability"] <= 1.0


def test_response_shape_matches_expected_example(client, png_bytes_sample):
    # Arrange
    expected_keys = set(json.loads(EXPECTED.read_text(encoding="utf-8")))
    # Act
    body = client.post("/predict", files={"file": ("rx.png", png_bytes_sample)}).json()
    # Assert
    assert expected_keys <= set(body)


def test_gradcam_url_is_served(client, png_bytes_sample):
    body = client.post("/predict", files={"file": ("rx.png", png_bytes_sample)}).json()
    image = client.get(body["gradcam_url"])
    assert image.status_code == 200
    assert image.content.startswith(b"\x89PNG")


def test_response_has_no_local_paths(client, dicom_bytes_sample, tmp_path):
    text = client.post("/predict", files={"file": ("rx.dcm", dicom_bytes_sample)}).text
    assert str(tmp_path) not in text
    assert "SECRETO-123" not in text


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("vacio.png", b""),
        ("texto.txt", b"hola"),
        ("corrupto.png", b"\x89PNG\r\n\x1a\nxx"),
        ("falso.dcm", b"\0" * 128 + b"DICMxx"),
        ("sin_extension", b"1234"),
    ],
)
def test_predict_invalid_returns_422(client, filename, content):
    response = client.post("/predict", files={"file": (filename, content)})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_predict_without_file_returns_422(client):
    assert client.post("/predict").status_code == 422


def test_predict_too_large_returns_422(client):
    big = b"\xff\xd8\xff" + b"0" * (2 * 1024 * 1024)
    response = client.post("/predict", files={"file": ("grande.jpg", big)})
    assert response.status_code == 422
    assert "MB" in response.text


def test_model_failure_returns_500_with_error(settings, png_bytes_sample):
    service = PneumoniaService(ExplodingClassifier())
    client = TestClient(create_app(lambda: service, settings), raise_server_exceptions=False)
    response = client.post("/predict", files={"file": ("rx.png", png_bytes_sample)})
    assert response.status_code == 500
    assert response.json() == {"error": "Error interno del modelo."}


def test_process_time_header(client):
    assert "X-Process-Time-ms" in client.get("/health").headers


def test_gradcam_files_are_pruned(settings, png_bytes_sample):
    from dataclasses import replace

    small = replace(settings, max_gradcam_files=2)
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    client = TestClient(create_app(lambda: service, small))
    for _ in range(4):
        client.post("/predict", files={"file": ("rx.png", png_bytes_sample)})
    assert len(list((small.static_dir / "gradcam").glob("*.png"))) == 2


def test_openapi_documents_predict(client):
    schema = client.get("/openapi.json").json()
    assert "/predict" in schema["paths"]
    assert "/health" in schema["paths"]
