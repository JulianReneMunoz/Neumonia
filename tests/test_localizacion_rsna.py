"""Fase 2: ¿Grad-CAM apunta a la lesión? Métricas contra las cajas de RSNA (spec 007). AAA.

Los mapas y las cajas son sintéticos: se sabe de antemano dónde "miró" el modelo y dónde está
la lesión, así que cada métrica tiene un resultado esperado exacto o con signo conocido.
"""

from __future__ import annotations

import csv
import json

import numpy as np
import pytest

from neumonia.controller.service import PneumoniaService
from neumonia.evaluation_localization import (
    Box,
    LocalizationCase,
    boxes_mask,
    build_cases,
    evaluate_localization,
    load_rsna_boxes,
    localization_scores,
    summarize,
    wilson_interval,
)
from tests.conftest import FakeClassifier, FakeExplainer, make_dicom_bytes
from tests.test_evaluation_and_data import RecordingTracker

GRID = 31


@pytest.fixture
def labels_csv(tmp_path):
    path = tmp_path / "stage_2_train_labels.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["patientId", "x", "y", "width", "height", "Target"])
        writer.writerows(
            [
                ["sano", "", "", "", "", 0],
                ["doble", 100, 200, 300, 400, 1],
                ["doble", 600, 200, 300, 400, 1],
                ["simple", 300, 300, 400, 400, 1],
                ["sin_imagen", 10, 10, 50, 50, 1],
            ]
        )
    return path


# --- Lectura de cajas y casos ----------------------------------------------------------------


def test_load_rsna_boxes_groups_by_patient_and_ignores_negatives(labels_csv):
    # Act
    boxes = load_rsna_boxes(labels_csv)
    # Assert
    assert set(boxes) == {"doble", "simple", "sin_imagen"}
    assert boxes["doble"] == [Box(100, 200, 300, 400), Box(600, 200, 300, 400)]


def test_load_boxes_from_adjudicated_export_keyed_by_sop_uid(tmp_path):
    # Arrange: exportación MD.ai convertida a CSV, una fila por caja y sin columna Target
    path = tmp_path / "rsna_boxes.csv"
    path.write_text(
        "\ufeffSOPInstanceUID,x,y,w,h\n1.2.3,10,20,30,40\n1.2.3,50,60,70,80\n4.5.6,1,2,3,4\n",
        encoding="utf-8",
    )
    # Act
    boxes = load_rsna_boxes(path)
    # Assert
    assert boxes["1.2.3"] == [Box(10, 20, 30, 40), Box(50, 60, 70, 80)]
    assert len(boxes["4.5.6"]) == 1


def test_load_boxes_rejects_unknown_format(tmp_path):
    path = tmp_path / "otro.csv"
    path.write_text("id_raro,x,y,width,height\n", encoding="utf-8")
    with pytest.raises(ValueError, match="identificador"):
        load_rsna_boxes(path)


def test_build_cases_requires_image_and_is_reproducible(labels_csv, tmp_path):
    # Arrange: DICOM en subcarpetas, como al descomprimir el zip
    images = tmp_path / "imgs"
    (images / "lote1").mkdir(parents=True)
    (images / "lote2").mkdir()
    (images / "lote1" / "doble.dcm").write_bytes(b"x")
    (images / "lote2" / "simple.dcm").write_bytes(b"x")
    # Act
    first = build_cases(labels_csv, images, seed=7)
    second = build_cases(labels_csv, images, seed=7)
    limited = build_cases(labels_csv, images, limit=1)
    # Assert
    assert {c.patient_id for c in first} == {"doble", "simple"}
    assert [c.patient_id for c in first] == [c.patient_id for c in second]
    assert len(limited) == 1


# --- Máscara de cajas ------------------------------------------------------------------------


def test_boxes_mask_rescales_from_original_resolution():
    # Arrange: caja de 1024×1024 → la mitad en 512×512
    box = Box(x=100, y=200, width=300, height=400)
    # Act
    mask = boxes_mask([box], rows=1024, cols=1024, size=512)
    # Assert
    rows, cols = np.nonzero(mask)
    assert (rows.min(), rows.max() + 1) == (100, 300)
    assert (cols.min(), cols.max() + 1) == (50, 200)


def test_boxes_mask_clips_boxes_outside_the_image():
    mask = boxes_mask([Box(900, 900, 500, 500)], rows=1024, cols=1024, size=64)
    assert mask[-1, -1]
    assert mask.sum() == pytest.approx((64 - 56) ** 2)


# --- Métricas --------------------------------------------------------------------------------


def _mask_center(size: int = 124) -> np.ndarray:
    mask = np.zeros((size, size), dtype=bool)
    mask[40:80, 40:80] = True
    return mask


def test_attention_on_the_lesion_scores_high():
    # Arrange: el modelo mira justo la caja
    cam = np.zeros((GRID, GRID))
    cam[11:19, 11:19] = 1.0
    # Act
    scores = localization_scores(cam, _mask_center())
    # Assert
    assert scores["hit"] == 1.0
    assert scores["enrichment"] > 3
    assert scores["iou"] > 0.5


def test_attention_on_a_marker_scores_below_chance():
    # Arrange: el modelo mira la esquina (marcador de lateralidad)
    cam = np.zeros((GRID, GRID))
    cam[0:4, 0:4] = 1.0
    # Act
    scores = localization_scores(cam, _mask_center())
    # Assert
    assert scores["hit"] == 0.0
    assert scores["enrichment"] < 1
    assert scores["iou"] == 0.0


def test_uniform_attention_equals_chance():
    scores = localization_scores(np.full((GRID, GRID), 0.3), _mask_center())
    assert scores["enrichment"] == pytest.approx(1.0, abs=0.02)
    assert scores["energy_in"] == pytest.approx(scores["area_fraction"], abs=0.01)


def test_empty_attention_scores_zero_without_dividing_by_zero():
    scores = localization_scores(np.zeros((GRID, GRID)), _mask_center())
    assert scores["hit"] == 0.0
    assert scores["enrichment"] == 0.0


@pytest.mark.parametrize(
    ("hits", "n", "low", "high"),
    [(0, 0, 0.0, 0.0), (8, 10, 0.49, 0.94), (50, 100, 0.40, 0.60)],
)
def test_wilson_interval_known_values(hits, n, low, high):
    lo, hi = wilson_interval(hits, n)
    assert lo == pytest.approx(low, abs=0.01)
    assert hi == pytest.approx(high, abs=0.01)


def test_summarize_reports_global_and_true_positive_subset():
    # Arrange
    rows = [
        {"label": "PNEUMONIA", "hit": 1.0, "area_fraction": 0.1, "energy_in": 0.4,
         "enrichment": 4.0, "iou": 0.3, "shortcut_warning": 0},
        {"label": "NORMAL", "hit": 0.0, "area_fraction": 0.1, "energy_in": 0.05,
         "enrichment": 0.5, "iou": 0.0, "shortcut_warning": 1},
    ]  # fmt: skip
    # Act
    summary = summarize(rows)
    # Assert
    assert summary["pointing_hit_rate"] == 0.5
    assert summary["tp_pointing_hit_rate"] == 1.0
    assert summary["tp_n"] == 1
    assert summary["shortcut_rate"] == 0.5
    assert summarize([]) == {"n": 0.0}


# --- Extremo a extremo con dobles -------------------------------------------------------------


def test_evaluate_localization_writes_results_and_logs_metrics(tmp_path, gradient_image):
    # Arrange: FakeExplainer mira el centro (celdas 10–20 de 31); una caja en el centro y otra
    # en la esquina; un DICOM corrupto que debe omitirse.
    (tmp_path / "centro.dcm").write_bytes(make_dicom_bytes(gradient_image))
    (tmp_path / "esquina.dcm").write_bytes(make_dicom_bytes(gradient_image))
    (tmp_path / "roto.dcm").write_bytes(b"no es un dicom")
    rows, cols = gradient_image.shape
    center = Box(cols * 0.3, rows * 0.3, cols * 0.4, rows * 0.4)
    corner = Box(0, 0, cols * 0.1, rows * 0.1)
    cases = [
        LocalizationCase("centro", str(tmp_path / "centro.dcm"), [center]),
        LocalizationCase("esquina", str(tmp_path / "esquina.dcm"), [corner]),
        LocalizationCase("roto", str(tmp_path / "roto.dcm"), [Box(0, 0, 10, 10)]),
    ]
    service = PneumoniaService(FakeClassifier((0.7, 0.2, 0.1)), FakeExplainer())
    tracker = RecordingTracker()
    # Act
    result = evaluate_localization(service, cases, tracker, tmp_path / "out")
    # Assert
    by_case = {row["case_id"]: row for row in result.rows}
    assert result.skipped == 1
    assert by_case["centro"]["hit"] == 1.0
    assert by_case["esquina"]["hit"] == 0.0
    assert by_case["centro"]["enrichment"] > 1 > by_case["esquina"]["enrichment"]
    assert tracker.params["n_cases"] == 3
    assert tracker.metrics["pointing_hit_rate"] == 0.5
    assert {"localizacion_por_caso.csv", "localizacion_resumen.json"} <= set(tracker.artifacts)
    saved = json.loads((tmp_path / "out" / "localizacion_resumen.json").read_text())
    assert saved["skipped"] == 1
    assert "SECRETO" not in (tmp_path / "out" / "localizacion_por_caso.csv").read_text()
