"""Reporte PDF, historial CSV, presentador de la vista y pasarelas."""

from __future__ import annotations

import csv

import httpx
import numpy as np
import pytest

from neumonia.config import Settings
from neumonia.controller.gateways import GatewayError, HttpGateway, LocalGateway, build_gateway
from neumonia.controller.report import (
    append_history,
    build_pdf_report,
    png_bytes,
    sanitize_patient_id,
)
from neumonia.domain import Label, Prediction
from neumonia.view.presenter import format_probability, present, validate_patient_id


@pytest.fixture
def prediction() -> Prediction:
    return Prediction(
        Label.PNEUMONIA,
        0.91,
        "viral",
        {"bacteriana": 0.05, "normal": 0.09, "viral": 0.86},
        heatmap=np.zeros((512, 512, 3), dtype=np.uint8),
        metadata={"age": 6, "sex": "F"},
    )


def test_pdf_report_is_valid_pdf(prediction):
    pdf = build_pdf_report(prediction, np.zeros((300, 300, 3), dtype=np.uint8), "1234567", "v1")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_pdf_report_without_heatmap(prediction):
    from dataclasses import replace

    pdf = build_pdf_report(
        replace(prediction, heatmap=None), np.zeros((50, 50, 3), np.uint8), "1", "v1"
    )
    assert pdf.startswith(b"%PDF")


def test_history_appends_rows_with_header(tmp_path, prediction):
    # Arrange
    path = tmp_path / "sub" / "historial.csv"
    # Act
    append_history(path, "123456", prediction)
    append_history(path, "654321", prediction)
    # Assert
    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0][1] == "paciente"
    assert len(rows) == 3
    assert rows[1][2] == "PNEUMONIA"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("123", "123"), ("  98-7 ", "98-7"), ("a/../b", "ab"), ("", "anonimo"), ("x" * 50, "x" * 32)],
)
def test_sanitize_patient_id(raw, expected):
    assert sanitize_patient_id(raw) == expected


def test_png_bytes():
    assert png_bytes(np.zeros((4, 4, 3), dtype=np.uint8)).startswith(b"\x89PNG")


@pytest.mark.parametrize(
    ("value", "text"), [(0.5, "50.00%"), (1.2, "100.00%"), (-1, "0.00%"), (0.98765, "98.77%")]
)
def test_format_probability(value, text):
    assert format_probability(value) == text


def test_present_pneumonia(prediction):
    view = present(prediction)
    assert view.color == "red"
    assert "NEUMONÍA" in view.headline
    assert view.subtype_text == "Viral"
    assert ("Edad (años)", "6") in view.metadata_rows


def test_present_normal():
    view = present(Prediction(Label.NORMAL, 0.9, "normal", {"normal": 0.9}))
    assert view.color == "green"
    assert view.subtype_text == "Sin hallazgos"


@pytest.mark.parametrize(
    ("raw", "ok"),
    [
        ("1234567", True),
        ("12345", True),
        ("", False),
        ("12ab5", False),
        ("1234", False),
        ("1" * 16, False),
    ],
)
def test_validate_patient_id(raw, ok):
    assert (validate_patient_id(raw) is None) is ok


def test_local_gateway(fake_service, png_bytes_sample):
    result = LocalGateway(fake_service).predict(png_bytes_sample, "rx.png")
    assert result.prediction.label is Label.PNEUMONIA
    assert result.original_rgb.shape == (256, 256, 3)


def _mock_api(status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/predict":
            if status != 200:
                return httpx.Response(status, json={"detail": "mal"})
            return httpx.Response(
                200,
                json={
                    "label": "NORMAL",
                    "probability": 0.8,
                    "gradcam_url": "/static/gradcam/a.png",
                    "subtype": "normal",
                    "class_probabilities": {"normal": 0.8},
                    "metadata": {},
                },
            )
        return httpx.Response(200, content=png_bytes(np.zeros((8, 8, 3), dtype=np.uint8)))

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_http_gateway_success(png_bytes_sample):
    result = HttpGateway("http://api:8000/", client=_mock_api()).predict(png_bytes_sample, "rx.png")
    assert result.prediction.label is Label.NORMAL
    assert result.prediction.heatmap.shape == (8, 8, 3)


def test_http_gateway_error(png_bytes_sample):
    with pytest.raises(GatewayError, match="422"):
        HttpGateway("http://api:8000", client=_mock_api(422)).predict(png_bytes_sample, "rx.png")


def test_build_gateway_uses_http_when_api_url_set():
    assert isinstance(build_gateway(Settings(api_url="http://api:8000")), HttpGateway)
