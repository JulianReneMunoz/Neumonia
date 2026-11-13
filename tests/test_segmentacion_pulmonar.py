"""Segmentación pulmonar real (spec 006, ADR-0008). Patrón AAA.

Casi todo se prueba sin PyTorch: la red se reemplaza por funciones que devuelven mapas sintéticos.
La prueba con PSPNet real lleva la marca `model` y se omite si el extra `seg` no está instalado.
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path

import numpy as np
import pytest

from neumonia.config import Settings
from neumonia.controller.factory import build_segmenter
from neumonia.controller.findings import describe
from neumonia.controller.service import PneumoniaService
from neumonia.domain import ZONE_NAMES, Findings, Label, LungMasks
from neumonia.model.localization import analyze_attention, zone_masks, zones_from_lungs
from neumonia.model.lung_segmentation import (
    PSPNET_TARGETS,
    GeometricLungSegmenter,
    IsolatedLungSegmenter,
    QualityCheckedSegmenter,
    XrvLungSegmenter,
    clean_mask,
    geometric_masks,
    quality_problem,
    resize_mask,
    verify_weights,
)
from neumonia.model.lung_worker import read_frame, serve, write_frame
from neumonia.view.overlays import DOMINANT_COLOR, OUT_SIZE, zones_overlay
from neumonia.view.presenter import present_findings
from tests.conftest import FakeClassifier, FakeExplainer

SAMPLES = Path(__file__).resolve().parents[1] / "artifacts" / "samples"


def ellipse(size: int, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size] / size
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0


def anatomic_lungs(size: int = 128) -> LungMasks:
    """Pulmones elípticos realistas: derecho del paciente a la izquierda de la imagen."""
    return LungMasks(
        right=ellipse(size, 0.30, 0.50, 0.14, 0.32),
        left=ellipse(size, 0.70, 0.52, 0.13, 0.30),
        source="pspnet",
    )


# --- Tipo de dominio --------------------------------------------------------------------------


def test_lung_masks_validates_shape_and_source():
    with pytest.raises(ValueError, match="misma forma"):
        LungMasks(np.zeros((4, 4), bool), np.zeros((5, 5), bool))
    with pytest.raises(ValueError, match="source"):
        LungMasks(np.zeros((4, 4), bool), np.zeros((4, 4), bool), source="sam3")


def test_label_grid_marks_right_as_1_and_left_as_2():
    # Act
    grid = np.asarray(anatomic_lungs().label_grid(64))
    # Assert
    assert grid.shape == (64, 64)
    assert set(np.unique(grid)) == {0, 1, 2}
    assert np.nonzero(grid == 1)[1].mean() < np.nonzero(grid == 2)[1].mean()


# --- Utilidades de máscara y control de calidad ----------------------------------------------


def test_geometric_segmenter_matches_previous_zones():
    # Arrange
    lungs = GeometricLungSegmenter().segment(np.zeros((64, 64, 3), np.uint8), size=100)
    # Act / Assert: compatibilidad con las zonas de la versión 0.4.0
    for name, mask in zones_from_lungs(lungs).items():
        assert np.array_equal(mask, zone_masks(100)[name])
    assert lungs.source == "geometrica"


def test_clean_mask_keeps_largest_component_and_fills_holes():
    # Arrange: un pulmón con un hueco y una mancha suelta
    mask = ellipse(100, 0.5, 0.5, 0.3, 0.3)
    mask[48:52, 48:52] = False
    mask[2:5, 2:5] = True
    # Act
    cleaned = clean_mask(mask)
    # Assert
    assert cleaned[50, 50]
    assert not cleaned[3, 3]


def test_clean_mask_of_empty_input_is_empty():
    assert not clean_mask(np.zeros((10, 10), bool)).any()


def test_resize_mask_keeps_boolean():
    resized = resize_mask(ellipse(64, 0.5, 0.5, 0.3, 0.3), 128)
    assert resized.shape == (128, 128)
    assert resized.dtype == bool


def test_quality_accepts_anatomic_lungs():
    assert quality_problem(anatomic_lungs()) is None


@pytest.mark.parametrize(
    ("lungs", "fragment"),
    [
        (
            LungMasks(ellipse(128, 0.3, 0.5, 0.03, 0.05), ellipse(128, 0.7, 0.5, 0.13, 0.3)),
            "un pulmón ocupa solo",
        ),
        (
            LungMasks(ellipse(128, 0.3, 0.5, 0.08, 0.17), ellipse(128, 0.7, 0.5, 0.08, 0.17)),
            "los pulmones ocupan solo",
        ),
        (
            LungMasks(ellipse(128, 0.7, 0.5, 0.13, 0.3), ellipse(128, 0.3, 0.5, 0.13, 0.3)),
            "invertidos",
        ),
        (
            LungMasks(ellipse(128, 0.45, 0.5, 0.2, 0.3), ellipse(128, 0.55, 0.5, 0.2, 0.3)),
            "se superponen",
        ),
    ],
    ids=["pulmon-pequeno", "area-total", "invertidos", "superpuestos"],
)
def test_quality_rejects_implausible_masks(lungs, fragment):
    assert fragment in quality_problem(lungs)


# --- Estrategias ----------------------------------------------------------------------------


def _fake_pspnet_probs(received: list[np.ndarray]):
    """PSPNet falsa: 'Right Lung' a la izquierda de la imagen, 'Left Lung' a la derecha."""

    def predict(image: np.ndarray) -> np.ndarray:
        received.append(image)
        probs = np.zeros((len(PSPNET_TARGETS), 512, 512), dtype=np.float32)
        probs[PSPNET_TARGETS.index("Right Lung")] = ellipse(512, 0.30, 0.5, 0.14, 0.32) * 0.9
        probs[PSPNET_TARGETS.index("Left Lung")] = ellipse(512, 0.70, 0.5, 0.13, 0.30) * 0.9
        return probs

    return predict


def test_xrv_segmenter_maps_anatomic_names_and_normalizes_input():
    # Arrange
    received: list[np.ndarray] = []
    segmenter = XrvLungSegmenter(predict_fn=_fake_pspnet_probs(received))
    pixels = np.full((300, 300, 3), 255, dtype=np.uint8)
    # Act
    lungs = segmenter.segment(pixels, size=128)
    # Assert
    assert lungs.source == "pspnet"
    assert lungs.right.shape == (128, 128)
    assert np.nonzero(lungs.right)[1].mean() < 64 < np.nonzero(lungs.left)[1].mean()
    assert received[0].shape == (512, 512)
    assert received[0].max() == pytest.approx(1024.0)  # escala de TorchXRayVision


def test_quality_checked_returns_primary_when_plausible():
    segmenter = QualityCheckedSegmenter(XrvLungSegmenter(predict_fn=_fake_pspnet_probs([])))
    lungs = segmenter.segment(np.zeros((64, 64, 3), np.uint8), size=128)
    assert lungs.source == "pspnet"
    assert lungs.note == ""


def test_quality_checked_falls_back_when_primary_fails():
    # Arrange
    def broken(_image):
        raise RuntimeError("pesos corruptos")

    segmenter = QualityCheckedSegmenter(XrvLungSegmenter(predict_fn=broken))
    # Act
    lungs = segmenter.segment(np.zeros((64, 64, 3), np.uint8), size=64)
    # Assert
    assert lungs.source == "geometrica"
    assert "pesos corruptos" in lungs.note


def test_quality_checked_falls_back_when_masks_are_implausible():
    # Arrange: la red "solo ve" un trozo pequeño de cada pulmón (consolidación densa)
    def tiny(_image):
        probs = np.zeros((len(PSPNET_TARGETS), 512, 512), dtype=np.float32)
        probs[PSPNET_TARGETS.index("Right Lung")] = ellipse(512, 0.3, 0.3, 0.04, 0.06)
        probs[PSPNET_TARGETS.index("Left Lung")] = ellipse(512, 0.7, 0.3, 0.04, 0.06)
        return probs

    segmenter = QualityCheckedSegmenter(XrvLungSegmenter(predict_fn=tiny))
    # Act
    lungs = segmenter.segment(np.zeros((64, 64, 3), np.uint8), size=64)
    # Assert
    assert lungs.source == "geometrica"
    assert lungs.note.startswith("Segmentación pspnet descartada")


def test_verify_weights_detects_tampering(tmp_path):
    # Arrange
    fake = tmp_path / "pesos.pth"
    fake.write_bytes(b"no son los pesos")
    # Act / Assert
    with pytest.raises(RuntimeError, match="SHA-256"):
        verify_weights(fake)
    verify_weights(tmp_path / "no-existe.pth")  # sin archivo: lo descargará TorchXRayVision


# --- Proceso aislado ------------------------------------------------------------------------


def test_worker_frames_roundtrip():
    buffer = io.BytesIO()
    write_frame(buffer, ("ok", {"a": np.arange(3)}))
    buffer.seek(0)
    status, payload = read_frame(buffer)
    assert status == "ok"
    assert payload["a"].tolist() == [0, 1, 2]


def test_worker_serve_answers_ok_and_errors_in_process():
    # Arrange: dos peticiones en el buzón
    inbox, outbox = io.BytesIO(), io.BytesIO()
    write_frame(inbox, (np.zeros((8, 8, 3), np.uint8), 64))
    write_frame(inbox, (np.zeros((8, 8, 3), np.uint8), 64))
    inbox.seek(0)
    # Act
    serve("tests.segmenter_doubles:FakePspnet", inbox, outbox)
    serve("tests.segmenter_doubles:broken_factory", io.BytesIO(_one_request()), outbox)
    # Assert
    outbox.seek(0)
    first, second, third = (read_frame(outbox) for _ in range(3))
    assert first[0] == "ok"
    assert first[1].source == "pspnet"
    assert second[0] == "ok"
    assert third == ("error", "ImportError: No module named 'torchxrayvision'")


def _one_request() -> bytes:
    buffer = io.BytesIO()
    write_frame(buffer, (np.zeros((8, 8, 3), np.uint8), 32))
    return buffer.getvalue()


def test_read_frame_detects_closed_channel():
    with pytest.raises(EOFError):
        read_frame(io.BytesIO(b"\x00\x01"))
    with pytest.raises(EOFError):
        read_frame(io.BytesIO(b"\x00\x00\x00\x00\x00\x00\x00\x10abc"))


@pytest.mark.slow
def test_isolated_segmenter_runs_in_child_process_and_recovers():
    # Arrange
    segmenter = IsolatedLungSegmenter("tests.segmenter_doubles:FakePspnet")
    pixels = np.zeros((64, 64, 3), np.uint8)
    try:
        # Act
        first = segmenter.segment(pixels, 96)
        pid = segmenter._process.pid
        segmenter._process.kill()
        segmenter._process.wait()
        second = segmenter.segment(pixels, 96)
        # Assert
        assert first.source == "pspnet"
        assert first.right.shape == (96, 96)
        assert second.source == "pspnet"
        assert segmenter._process.pid != pid  # se recreó el proceso hijo
    finally:
        segmenter.close()


@pytest.mark.slow
def test_isolated_segmenter_propagates_child_errors():
    segmenter = IsolatedLungSegmenter("tests.segmenter_doubles:ExplodingSegmenter")
    try:
        with pytest.raises(RuntimeError, match="imagen ilegible"):
            segmenter.segment(np.zeros((8, 8, 3), np.uint8), 32)
    finally:
        segmenter.close()


# --- Zonas, informe, servicio y configuración ------------------------------------------------


def test_zones_follow_each_lung_own_height():
    # Arrange
    lungs = anatomic_lungs()
    # Act
    zones = zones_from_lungs(lungs)
    # Assert: disjuntas, dentro del pulmón y cubriéndolo por completo
    stacked = np.stack(list(zones.values())).astype(int).sum(axis=0)
    assert stacked.max() == 1
    assert np.array_equal(stacked.astype(bool), lungs.lung_field)
    right_rows = np.nonzero(lungs.right.any(axis=1))[0]
    assert np.nonzero(zones["derecho_superior"].any(axis=1))[0].min() == right_rows.min()
    assert np.nonzero(zones["derecho_inferior"].any(axis=1))[0].max() == right_rows.max()


def test_analyze_attention_uses_given_lungs():
    # Arrange: atención en la base del pulmón izquierdo del paciente (derecha de la imagen)
    lungs = anatomic_lungs(124)
    cam = np.zeros((31, 31))
    cam[18:24, 19:25] = 1.0
    # Act
    findings = analyze_attention(cam, lungs=lungs)
    # Assert
    assert findings.lung_source == "pspnet"
    assert findings.dominant_zone.startswith("izquierdo")
    assert np.asarray(findings.lung_grid).shape == (64, 64)


def test_findings_roundtrip_keeps_segmentation_fields():
    findings = analyze_attention(np.ones((31, 31)) * 0.3, lungs=anatomic_lungs(124))
    restored = Findings.from_dict(findings.to_dict())
    assert restored.lung_source == "pspnet"
    assert restored.lung_grid == findings.lung_grid


def test_describe_mentions_segmentation_source_or_fallback_note():
    # Arrange
    segmented = analyze_attention(np.ones((31, 31)) * 0.6, lungs=anatomic_lungs(124))
    fallback = analyze_attention(
        np.ones((31, 31)) * 0.6, lungs=geometric_masks(124, note="Segmentación descartada: x.")
    )
    # Act
    text_seg = " ".join(describe(segmented, Label.PNEUMONIA, 0.9, "viral"))
    text_fb = " ".join(describe(fallback, Label.PNEUMONIA, 0.9, "viral"))
    # Assert
    assert "silueta pulmonar segmentada" in text_seg
    assert "área pulmonar segmentada" in text_seg
    assert "Segmentación descartada: x." in text_fb
    assert "área pulmonar aproximada" in text_fb


class SpySegmenter:
    name = "espia"

    def __init__(self) -> None:
        self.calls = 0

    def segment(self, pixels, size=512):
        self.calls += 1
        return LungMasks(*_two_lungs(size), source="pspnet")


def _two_lungs(size):
    lungs = anatomic_lungs(size)
    return lungs.right, lungs.left


def test_service_uses_injected_segmenter_only_when_explaining(png_bytes_sample):
    # Arrange
    spy = SpySegmenter()
    service = PneumoniaService(FakeClassifier(), FakeExplainer(), segmenter=spy)
    # Act
    explained = service.predict_bytes(png_bytes_sample, "rx.png")
    service.predict_bytes(png_bytes_sample, "rx.png", explain=False)
    # Assert
    assert spy.calls == 1
    assert explained.findings.lung_source == "pspnet"


def test_build_segmenter_from_settings():
    assert isinstance(build_segmenter(Settings()), GeometricLungSegmenter)
    pspnet = build_segmenter(Settings(lung_segmenter="pspnet"))
    assert isinstance(pspnet, QualityCheckedSegmenter)
    assert isinstance(pspnet.primary, IsolatedLungSegmenter)
    assert pspnet.primary._process is None  # el proceso hijo se crea solo al usarlo


def test_settings_reads_segmenter_from_env(monkeypatch):
    monkeypatch.setenv("NEUMONIA_LUNG_SEGMENTER", "PSPNet")
    assert Settings.from_env().lung_segmenter == "pspnet"
    with pytest.raises(ValueError, match="lung_segmenter"):
        Settings(lung_segmenter="sam3")


# --- Vista ----------------------------------------------------------------------------------


def test_zones_overlay_tints_lungs_and_highlights_dominant_zone():
    # Arrange
    lungs = anatomic_lungs(128)
    base = np.full((256, 256, 3), 40, dtype=np.uint8)
    # Act
    image = zones_overlay(base, lungs.label_grid(), "izquierdo_inferior")
    # Assert
    assert image.shape == (OUT_SIZE, OUT_SIZE, 3)
    assert image.dtype == np.uint8
    assert tuple(image[5, 5]) == (40, 40, 40)  # fuera de los pulmones no cambia
    lower_left_lung = image[int(0.72 * OUT_SIZE), int(0.70 * OUT_SIZE)].astype(int)
    assert lower_left_lung[0] > lower_left_lung[2]  # tinte naranja de la zona dominante
    assert DOMINANT_COLOR[0] > DOMINANT_COLOR[2]


def test_zones_overlay_accepts_grayscale_and_rejects_empty_grid():
    gray = np.zeros((50, 50), dtype=np.uint8)
    assert zones_overlay(gray, anatomic_lungs(64).label_grid()).shape == (OUT_SIZE, OUT_SIZE, 3)
    with pytest.raises(ValueError, match="lung_grid"):
        zones_overlay(gray, [])


def test_present_findings_shows_segmentation_source():
    view = present_findings(analyze_attention(np.ones((31, 31)) * 0.3, lungs=anatomic_lungs(124)))
    assert view.segmentation == "Silueta pulmonar segmentada (PSPNet)"
    assert view.segmentation_note == ""


# --- PSPNet real (extra `seg`) ----------------------------------------------------------------


@pytest.mark.model
@pytest.mark.slow
@pytest.mark.skipif(
    importlib.util.find_spec("torchxrayvision") is None,
    reason="requiere el extra `seg` (make seg)",
)
def test_real_pspnet_segments_course_sample():
    # find_spec no importa el paquete: PyTorch nunca debe cargarse junto a TensorFlow (ADR-0008).
    from neumonia.model.readers import read_path

    # Arrange
    image = read_path(SAMPLES / "person1711_bacteria_4527.jpeg")
    segmenter = QualityCheckedSegmenter(IsolatedLungSegmenter())
    try:
        # Act
        lungs = segmenter.segment(image.pixels)
    finally:
        segmenter.primary.close()
    # Assert: convención anatómica confirmada y control de calidad superado
    assert lungs.source == "pspnet", lungs.note
    assert np.nonzero(lungs.right)[1].mean() < np.nonzero(lungs.left)[1].mean()
    assert set(zones_from_lungs(lungs)) == set(ZONE_NAMES)
