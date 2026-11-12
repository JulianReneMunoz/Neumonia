"""Preprocesamiento: paridad con el entrenamiento (512×512, gris, CLAHE, [0,1])."""

from __future__ import annotations

import numpy as np
import pytest

from neumonia.model.preprocessing import apply_clahe, preprocess, resize_for_display, to_gray


@pytest.mark.parametrize(
    "shape", [(100, 100, 3), (1024, 1024, 3), (300, 700, 3), (512, 512, 3), (64, 64)]
)
def test_preprocess_output_shape_and_range(shape):
    # Arrange
    image = np.random.default_rng(0).integers(0, 256, size=shape, dtype=np.uint8)
    # Act
    tensor = preprocess(image)
    # Assert
    assert tensor.shape == (1, 512, 512, 1)
    assert tensor.dtype == np.float32
    assert tensor.min() >= 0.0
    assert tensor.max() <= 1.0


def test_preprocess_is_deterministic():
    image = np.random.default_rng(1).integers(0, 256, size=(256, 256, 3), dtype=np.uint8)
    np.testing.assert_array_equal(preprocess(image), preprocess(image))


def test_preprocess_rejects_float_input():
    with pytest.raises(ValueError, match="uint8"):
        preprocess(np.zeros((10, 10, 3), dtype=np.float32))


def test_preprocess_custom_size():
    image = np.full((50, 50, 3), 128, dtype=np.uint8)
    assert preprocess(image, size=64).shape == (1, 64, 64, 1)


def test_clahe_increases_local_contrast():
    # Arrange: imagen de bajo contraste
    low = np.tile(np.linspace(100, 140, 128, dtype=np.uint8), (128, 1))
    # Act
    equalized = apply_clahe(low)
    # Assert
    assert equalized.std() > low.std()


def test_to_gray_accepts_2d_and_3_channels():
    gray = np.ones((5, 5), dtype=np.uint8)
    assert to_gray(gray) is gray
    assert to_gray(np.ones((5, 5, 3), dtype=np.uint8)).shape == (5, 5)


def test_to_gray_rejects_4_channels():
    with pytest.raises(ValueError, match=r"\(H, W, 3\)"):
        to_gray(np.ones((5, 5, 4), dtype=np.uint8))


def test_resize_for_display():
    assert resize_for_display(np.ones((10, 20, 3), dtype=np.uint8)).shape == (512, 512, 3)
