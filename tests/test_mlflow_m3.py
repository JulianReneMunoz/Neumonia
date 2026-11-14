"""SPEC-013: tres corridas comparables (umbral y preprocesamiento) con calidad y latencia."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from neumonia.model.preprocessing import preprocess
from neumonia.tracking.m3_runs import (
    RUNS,
    LabeledImage,
    confusion,
    label_from_course_path,
    latency_summary,
    preprocess_variant,
    run_config,
    sample_items,
)


def _png(path: Path, value: int) -> Path:
    img = np.full((64, 64, 3), value, dtype=np.uint8)
    img[16:48, 16:48] = 255 - value
    cv2.imwrite(str(path), img)
    return path


def test_the_three_runs_change_one_thing_each():
    # Arrange
    base, threshold, plain = RUNS
    # Assert: misma configuración salvo un factor
    assert (base.threshold, base.clahe) == (0.5, True)
    assert (threshold.threshold, threshold.clahe) == (0.3, True)
    assert (plain.threshold, plain.clahe) == (0.5, False)
    assert len({r.name for r in RUNS}) == 3
    assert "CLAHE" in base.preprocessing
    assert "sin CLAHE" in plain.preprocessing


def test_clahe_variant_is_identical_to_the_serving_preprocessing():
    # Arrange
    rng = np.random.default_rng(0)
    pixels = rng.integers(0, 255, (100, 120, 3), dtype=np.uint8)
    # Act
    with_clahe = preprocess_variant(pixels, clahe=True)
    without = preprocess_variant(pixels, clahe=False)
    # Assert
    np.testing.assert_array_equal(with_clahe, preprocess(pixels))
    assert without.shape == with_clahe.shape == (1, 512, 512, 1)
    assert not np.array_equal(without, with_clahe)
    assert without.min() >= 0.0
    assert without.max() <= 1.0


def test_latency_summary_reports_mean_p95_and_throughput():
    # Act
    stats = latency_summary([10.0, 20.0, 30.0, 40.0, 100.0])
    # Assert
    assert stats["latency_mean_ms"] == 40.0
    assert stats["latency_p50_ms"] == 30.0
    assert stats["latency_p95_ms"] == pytest.approx(88.0)
    assert stats["throughput_img_s"] == 25.0
    with pytest.raises(ValueError, match="latencias"):
        latency_summary([])


@pytest.mark.parametrize(
    ("name", "target"),
    [
        ("JPG/normal/IM-0001.jpeg", 0),
        ("DICOM/normal (2).dcm", 0),
        ("JPG/bacteria/person1_bacteria_1.jpeg", 1),
        ("DICOM/viral (3).dcm", 1),
        ("otros/radiografia.png", None),
    ],
)
def test_course_labels_come_from_the_folder_or_file_name(name, target):
    assert label_from_course_path(Path(name)) == target


def test_sample_is_reproducible_and_keeps_both_classes():
    # Arrange
    items = [LabeledImage(Path(f"{i:03d}.dcm"), int(i < 30)) for i in range(100)]
    # Act
    first = sample_items(items, 20, seed=42)
    second = sample_items(items, 20, seed=42)
    # Assert
    assert first == second
    assert len(first) == 20
    assert sum(i.target for i in first) == 6  # 30 % de positivos, como el total
    assert sample_items(items, None, seed=1) == sorted(items, key=lambda i: str(i.path))


def test_run_config_measures_quality_latency_and_skips_unreadable(tmp_path):
    # Arrange: el "modelo" ve neumonía cuando la imagen es oscura
    items = [
        LabeledImage(_png(tmp_path / "a.png", 20), 1),
        LabeledImage(_png(tmp_path / "b.png", 220), 0),
        LabeledImage(_png(tmp_path / "c.png", 30), 1),
        LabeledImage(tmp_path / "falta.png", 0),
    ]

    def fake_model(tensor: np.ndarray) -> np.ndarray:
        dark = float(tensor.mean()) < 0.5
        return np.array([0.6, 0.2, 0.2]) if dark else np.array([0.1, 0.8, 0.1])

    ticks = iter([0.0, 0.01, 1.0, 1.02, 2.0, 2.03])
    # Act
    result = run_config(fake_model, items, RUNS[0], clock=lambda: next(ticks))
    # Assert
    m = result.metrics
    assert result.skipped == 1
    assert m["n"] == 3
    assert m["accuracy"] == 1.0
    assert m["roc_auc"] == 1.0
    assert m["latency_mean_ms"] == pytest.approx(20.0)
    assert [r["pred"] for r in result.rows] == [1, 0, 1]
    assert confusion(result.rows) == [[1, 0], [0, 2]]
    assert all("PatientID" not in r and "PatientName" not in r for r in result.rows)


def test_run_config_fails_clearly_when_nothing_can_be_read(tmp_path):
    with pytest.raises(ValueError, match="Ninguna imagen"):
        run_config(
            lambda t: np.array([0.3, 0.4, 0.3]), [LabeledImage(tmp_path / "x.png", 1)], RUNS[0]
        )
