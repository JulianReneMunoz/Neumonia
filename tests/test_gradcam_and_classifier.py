"""Grad-CAM y clasificador Keras con una red mínima (rápido, sin el modelo de 118 MB)."""

from __future__ import annotations

import numpy as np
import pytest

from neumonia.model.classifier import KerasClassifier, ModelNotFoundError, load_keras_model
from neumonia.model.gradcam import GradCamExplainer, normalize_heatmap, overlay_heatmap


@pytest.mark.parametrize(
    ("raw", "expected_max"),
    [(np.array([[1.0, 2.0], [3.0, 4.0]]), 1.0), (np.array([[-1.0, 2.0]]), 1.0)],
)
def test_normalize_heatmap(raw, expected_max):
    heat = normalize_heatmap(raw)
    assert heat.max() == pytest.approx(expected_max)
    assert heat.min() >= 0.0


@pytest.mark.parametrize("raw", [np.zeros((3, 3)), -np.ones((3, 3)), np.full((2, 2), np.nan)])
def test_normalize_heatmap_degenerate_returns_zeros(raw):
    assert not normalize_heatmap(raw).any()


@pytest.mark.parametrize("base_shape", [(100, 80, 3), (1024, 1024, 3), (64, 64)])
def test_overlay_heatmap_shape(base_shape):
    base = np.full(base_shape, 90, dtype=np.uint8)
    out = overlay_heatmap(np.random.default_rng(0).random((31, 31)), base)
    assert out.shape == (512, 512, 3)
    assert out.dtype == np.uint8


def test_overlay_highlights_hot_region():
    # Arrange: calor solo en la esquina superior izquierda
    heat = np.zeros((31, 31))
    heat[:5, :5] = 1.0
    base = np.zeros((512, 512, 3), dtype=np.uint8)
    # Act
    out = overlay_heatmap(heat, base)
    # Assert: en JET la zona caliente tira a rojo y la fría a azul
    hot, cold = out[10, 10].astype(int), out[500, 500].astype(int)
    assert hot[0] > cold[0]  # más rojo
    assert cold[2] > hot[2]  # más azul


def test_missing_model_raises_clear_error(tmp_path):
    classifier = KerasClassifier(tmp_path / "no-existe.h5")
    with pytest.raises(ModelNotFoundError, match="make model"):
        classifier.predict_proba(np.zeros((1, 512, 512, 1), dtype=np.float32))


@pytest.mark.slow
def test_keras_classifier_with_tiny_model(tiny_keras_model):
    # Arrange
    classifier = KerasClassifier(tiny_keras_model)
    batch = np.random.default_rng(0).random((1, 512, 512, 1), dtype=np.float32)
    # Act
    probs = classifier.predict_proba(batch)
    # Assert
    assert classifier.is_loaded
    assert probs.shape == (3,)
    assert probs.sum() == pytest.approx(1.0)


@pytest.mark.slow
def test_keras_classifier_rejects_wrong_number_of_classes(tiny_keras_model):
    classifier = KerasClassifier(tiny_keras_model, class_names=("a", "b"))
    with pytest.raises(ValueError, match="salidas"):
        _ = classifier.model


@pytest.mark.slow
def test_model_is_cached(tiny_keras_model):
    assert load_keras_model(str(tiny_keras_model)) is load_keras_model(str(tiny_keras_model))


@pytest.mark.slow
@pytest.mark.parametrize("class_index", [0, 1, 2])
def test_gradcam_explainer_with_tiny_model(tiny_keras_model, class_index):
    model = load_keras_model(str(tiny_keras_model))
    explainer = GradCamExplainer(model)
    batch = np.random.default_rng(class_index).random((1, 512, 512, 1), dtype=np.float32)
    heat = explainer.explain(batch, class_index)
    assert heat.ndim == 2
    assert heat.min() >= 0.0
    assert heat.max() <= 1.0


@pytest.mark.slow
def test_gradcam_unknown_layer(tiny_keras_model):
    with pytest.raises(ValueError, match="no_existe"):
        GradCamExplainer(load_keras_model(str(tiny_keras_model)), layer_name="no_existe")
