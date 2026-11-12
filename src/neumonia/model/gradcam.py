"""Explicabilidad con Grad-CAM (Selvaraju et al., 2017) usando `tf.GradientTape`.

Reemplaza `K.gradients` + `disable_eager_execution` del monolito (API de TF1 que ya no
existe en Keras 3). Corrige además un defecto del original: el monolito ponderaba solo 64
de los 128 filtros de `conv10_thisone`; aquí se ponderan todos.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import cv2
import numpy as np

from neumonia.config import GRADCAM_LAYER, IMG_SIZE

OVERLAY_ALPHA = 0.8  # mismo factor `hif` del monolito


@runtime_checkable
class Explainer(Protocol):
    def explain(self, batch: np.ndarray, class_index: int) -> np.ndarray:
        """Devuelve un mapa de calor 2D float en [0, 1]."""
        ...


def normalize_heatmap(raw: np.ndarray) -> np.ndarray:
    heat = np.maximum(np.asarray(raw, dtype=np.float64), 0)  # ReLU
    peak = heat.max() if heat.size else 0.0
    if peak <= 0 or not np.isfinite(peak):
        return np.zeros_like(heat, dtype=np.float64)
    return heat / peak


def overlay_heatmap(
    heatmap: np.ndarray, image_bgr: np.ndarray, size: int = IMG_SIZE, alpha: float = OVERLAY_ALPHA
) -> np.ndarray:
    """Superpone el mapa (colormap JET) sobre la radiografía. Devuelve RGB uint8 (size, size, 3)."""
    base = cv2.resize(image_bgr, (size, size))
    if base.ndim == 2:
        base = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)
    heat = cv2.resize(normalize_heatmap(heatmap).astype(np.float32), (size, size))
    colored = cv2.applyColorMap(np.uint8(255 * heat), cv2.COLORMAP_JET)
    transparency = (colored * alpha).astype(np.uint8)
    blended = cv2.add(transparency, base)
    return blended[:, :, ::-1].copy()  # BGR → RGB


class GradCamExplainer:
    """Grad-CAM sobre la última capa convolucional del modelo Keras."""

    def __init__(self, keras_model: Any, layer_name: str = GRADCAM_LAYER) -> None:
        import tensorflow as tf

        self._tf = tf
        layer = keras_model.get_layer(layer_name)
        self._grad_model = tf.keras.Model(
            keras_model.inputs, [layer.output, keras_model.outputs[0]]
        )
        self.layer_name = layer_name

    def explain(self, batch: np.ndarray, class_index: int) -> np.ndarray:
        tf = self._tf
        inputs = tf.convert_to_tensor(batch, dtype=tf.float32)
        with tf.GradientTape() as tape:
            conv_output, predictions = self._grad_model([inputs], training=False)
            score = predictions[:, class_index]
        grads = tape.gradient(score, conv_output)
        pooled = tf.reduce_mean(grads, axis=(0, 1, 2))  # peso de cada filtro
        cam = tf.reduce_sum(conv_output[0] * pooled, axis=-1)
        return normalize_heatmap(cam.numpy())
