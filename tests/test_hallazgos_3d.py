"""Informe de hallazgos asistido y vistas 3D (spec 005, ADR-0007).

Patrón AAA: Arrange (mapa de atención sintético) → Act → Assert.
Los mapas sintéticos permiten fijar dónde "miró" el modelo y comprobar la traducción a zonas.
"""

from __future__ import annotations

import httpx
import numpy as np
import plotly.graph_objects as go
import pytest
from fastapi.testclient import TestClient

from neumonia.api.app import create_app
from neumonia.controller.findings import NOTE, describe, with_summary
from neumonia.controller.gateways import HttpGateway
from neumonia.controller.report import build_pdf_report, png_bytes
from neumonia.controller.service import PneumoniaService
from neumonia.domain import ZONE_NAMES, Findings, Label, Prediction
from neumonia.model.localization import (
    analyze_attention,
    classify_laterality,
    lung_field,
    zone_masks,
)
from neumonia.view.presenter import present_findings
from neumonia.view.visual3d import attention_surface_figure, lungs_3d_figure
from tests.conftest import FakeClassifier, FakeExplainer

GRID = 31


def _cam_with_block(rows: slice, cols: slice) -> np.ndarray:
    cam = np.zeros((GRID, GRID))
    cam[rows, cols] = 1.0
    return cam


# --- Localización por zonas -------------------------------------------------------------------


def test_zone_masks_are_six_disjoint_regions_inside_the_image():
    # Act
    masks = zone_masks(100)
    # Assert
    assert tuple(masks) == ZONE_NAMES
    stacked = np.stack(list(masks.values())).astype(int).sum(axis=0)
    assert stacked.max() == 1  # sin solapamiento
    assert all(mask.any() for mask in masks.values())


def test_lung_field_is_union_of_zones_and_excludes_borders():
    # Act
    field = lung_field(100)
    # Assert
    assert not field[0, :].any()
    assert not field[:, 0].any()
    assert field[50, 25]
    assert field[50, 75]
    assert not field[50, 50]  # mediastino


@pytest.mark.parametrize(
    ("right", "left", "expected"),
    [
        (0.6, 0.1, "derecho"),
        (0.1, 0.6, "izquierdo"),
        (0.5, 0.45, "bilateral"),
        (0.05, 0.1, "sin_foco"),
    ],
)
def test_classify_laterality(right, left, expected):
    assert classify_laterality(right, left) == expected


def test_attention_on_image_left_lower_is_patient_right_lower():
    # Arrange: bloque en la mitad izquierda de la imagen, tercio inferior de los campos
    cam = _cam_with_block(slice(21, 26), slice(5, 12))
    # Act
    findings = analyze_attention(cam, size=124)
    # Assert (convención radiológica: izquierda de la imagen = pulmón derecho del paciente)
    assert findings.dominant_zone == "derecho_inferior"
    assert findings.laterality == "derecho"
    assert findings.extent_pct > 0
    assert not findings.shortcut_warning


def test_attention_outside_lungs_triggers_shortcut_warning():
    # Arrange: atención solo en la franja superior (marcadores / bordes)
    cam = _cam_with_block(slice(0, 3), slice(0, GRID))
    # Act
    findings = analyze_attention(cam, size=124)
    # Assert
    assert findings.shortcut_warning
    assert findings.outside_inside_ratio >= 1.0
    assert findings.out_of_lung_pct > 50
    assert np.isfinite(findings.outside_inside_ratio)


def test_uniform_attention_has_density_ratio_close_to_one():
    findings = analyze_attention(np.full((GRID, GRID), 0.4), size=124)
    assert findings.outside_inside_ratio == pytest.approx(1.0, abs=0.02)


@pytest.mark.parametrize("cam", [np.zeros((GRID, GRID)), np.full((GRID, GRID), np.nan)])
def test_empty_or_nan_attention_has_no_focus_and_no_warning(cam):
    # Act
    findings = analyze_attention(cam, size=62)
    # Assert
    assert findings.dominant_zone == ""
    assert findings.laterality == "sin_foco"
    assert not findings.shortcut_warning
    assert findings.out_of_lung_pct == 0.0


def test_attention_grid_keeps_original_resolution():
    findings = analyze_attention(_cam_with_block(slice(10, 20), slice(10, 20)), size=62)
    assert np.asarray(findings.attention_grid).shape == (GRID, GRID)


# --- Redacción del informe --------------------------------------------------------------------


@pytest.fixture
def right_lower_findings() -> Findings:
    return analyze_attention(_cam_with_block(slice(21, 26), slice(5, 12)), size=124)


def test_describe_pneumonia_mentions_subtype_zone_and_note(right_lower_findings):
    # Act
    lines = describe(right_lower_findings, Label.PNEUMONIA, 0.93, "viral")
    # Assert
    text = " ".join(lines)
    assert "patrón viral" in text
    assert "93.0%" in text
    assert "campo inferior del pulmón derecho" in text
    assert lines[-1] == NOTE
    assert not any("Advertencia" in line for line in lines)


def test_describe_normal_and_shortcut_warning():
    # Arrange
    findings = analyze_attention(_cam_with_block(slice(0, 3), slice(0, GRID)), size=124)
    # Act
    lines = describe(findings, Label.NORMAL, 0.8, "normal")
    # Assert
    assert lines[0].startswith("El modelo no sugiere")
    assert any(line.startswith("Advertencia de calidad") for line in lines)


def test_describe_diffuse_attention_has_no_grammar_glitch():
    # Arrange: atención baja y homogénea dentro de los pulmones
    findings = analyze_attention(np.full((GRID, GRID), 0.1), size=124)
    # Act
    text = " ".join(describe(findings, Label.PNEUMONIA, 0.7, "bacteriana"))
    # Assert
    assert "difusa, sin un foco definido" in text
    assert "con sin" not in text


def test_with_summary_returns_new_findings(right_lower_findings):
    enriched = with_summary(right_lower_findings, Label.PNEUMONIA, 0.9, "bacteriana")
    assert enriched.summary
    assert not right_lower_findings.summary


def test_findings_roundtrip_dict(right_lower_findings):
    # Arrange
    enriched = with_summary(right_lower_findings, Label.PNEUMONIA, 0.9, "viral")
    # Act
    restored = Findings.from_dict(enriched.to_dict())
    # Assert
    assert restored.dominant_zone == enriched.dominant_zone
    assert restored.laterality == enriched.laterality
    assert restored.summary == enriched.summary
    assert restored.zone_attention.keys() == enriched.zone_attention.keys()
    assert np.asarray(restored.attention_grid).shape == (GRID, GRID)


# --- Servicio, API, pasarela y PDF ------------------------------------------------------------


def test_service_attaches_findings(fake_service, png_bytes_sample):
    # Act
    prediction = fake_service.predict_bytes(png_bytes_sample, "rx.png")
    # Assert
    assert prediction.findings is not None
    assert prediction.findings.summary
    assert prediction.to_contract("/x.png", "v1")["findings"]["dominant_zone"] in ZONE_NAMES


def test_service_without_explainer_has_no_findings(png_bytes_sample):
    prediction = PneumoniaService(FakeClassifier(), None).predict_bytes(png_bytes_sample, "rx.png")
    assert prediction.findings is None
    assert prediction.to_contract(None, "v1")["findings"] is None


def test_api_predict_includes_findings(settings, png_bytes_sample):
    # Arrange
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    client = TestClient(create_app(service_factory=lambda: service, settings=settings))
    # Act
    body = client.post("/predict", files={"file": ("rx.png", png_bytes_sample)}).json()
    # Assert: campos previos intactos (cambio aditivo) + findings
    assert {"label", "probability", "gradcam_url"} <= body.keys()
    assert set(body["findings"]["zone_attention"]) == set(ZONE_NAMES)
    assert isinstance(body["findings"]["summary"], list)


def test_http_gateway_parses_findings(png_bytes_sample, right_lower_findings):
    # Arrange
    payload = right_lower_findings.to_dict()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/predict":
            return httpx.Response(
                200,
                json={
                    "label": "PNEUMONIA",
                    "probability": 0.9,
                    "gradcam_url": "/static/gradcam/a.png",
                    "subtype": "viral",
                    "class_probabilities": {"viral": 0.9},
                    "metadata": {},
                    "findings": payload,
                },
            )
        return httpx.Response(200, content=png_bytes(np.zeros((8, 8, 3), dtype=np.uint8)))

    gateway = HttpGateway(
        "http://api:8000", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    # Act
    result = gateway.predict(png_bytes_sample, "rx.png")
    # Assert
    assert result.prediction.findings is not None
    assert result.prediction.findings.dominant_zone == "derecho_inferior"


def test_pdf_report_with_findings_is_valid_and_larger(right_lower_findings):
    # Arrange
    base = Prediction(Label.PNEUMONIA, 0.9, "viral", {"viral": 0.9}, heatmap=None)
    enriched = Prediction(
        Label.PNEUMONIA,
        0.9,
        "viral",
        {"viral": 0.9},
        heatmap=None,
        findings=with_summary(right_lower_findings, Label.PNEUMONIA, 0.9, "viral"),
    )
    original = np.zeros((64, 64, 3), dtype=np.uint8)
    # Act
    plain = build_pdf_report(base, original, "123", "v1")
    detailed = build_pdf_report(enriched, original, "123", "v1")
    # Assert
    assert detailed.startswith(b"%PDF")
    assert len(detailed) > len(plain)


# --- Vista: presentador y figuras 3D ----------------------------------------------------------


def test_present_findings_marks_single_dominant_zone(right_lower_findings):
    # Act
    view = present_findings(right_lower_findings)
    # Assert
    assert len(view.zone_rows) == 6
    assert [row[2] for row in view.zone_rows].count(True) == 1
    assert view.laterality
    assert view.extent.endswith("%")
    assert "razón" in view.outside


def test_attention_surface_figure_has_base_and_relief(right_lower_findings):
    # Act
    figure = attention_surface_figure(
        np.zeros((300, 300, 3), dtype=np.uint8), right_lower_findings.attention_grid
    )
    # Assert
    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 2
    assert all(isinstance(trace, go.Surface) for trace in figure.data)


@pytest.mark.parametrize("grid", [[], [1.0, 2.0]])
def test_attention_surface_figure_rejects_invalid_grid(grid):
    with pytest.raises(ValueError, match="matriz 2D"):
        attention_surface_figure(np.zeros((32, 32, 3), dtype=np.uint8), grid)


def test_lungs_3d_figure_two_lungs_and_six_labels(right_lower_findings):
    # Act
    figure = lungs_3d_figure(right_lower_findings.zone_attention)
    # Assert
    assert len(figure.data) == 2
    assert len(figure.layout.scene.annotations) == 6


def test_lungs_3d_figure_handles_zero_attention():
    figure = lungs_3d_figure(dict.fromkeys(ZONE_NAMES, 0.0))
    assert figure.data[0].cmax == pytest.approx(0.25)
