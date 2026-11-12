"""Preprocesamiento idéntico al del entrenamiento de conv_MLP_84.

512×512 → escala de grises → CLAHE (clip 2.0, rejilla 4×4) → [0, 1] → (1, 512, 512, 1).
Cambiar cualquiera de estos pasos rompe la paridad entrenamiento/servicio (training-serving
skew), una de las deudas técnicas descritas por Sculley et al. (2015).
"""

from __future__ import annotations

import cv2
import numpy as np

from neumonia.config import IMG_SIZE

CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID = (4, 4)


def to_gray(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        return array
    if array.ndim == 3 and array.shape[2] == 3:
        return cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)
    raise ValueError(f"Se esperaba una imagen 2D o (H, W, 3); llegó {array.shape}.")


def apply_clahe(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
    return clahe.apply(gray)


def resize_for_display(array: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    return cv2.resize(array, (size, size))


def preprocess(array: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    """Devuelve el tensor listo para el modelo: float32 (1, size, size, 1) en [0, 1]."""
    if array.dtype != np.uint8:
        raise ValueError("preprocess espera uint8 (use readers.to_uint8 antes).")
    resized = cv2.resize(array, (size, size))
    equalized = apply_clahe(to_gray(resized))
    tensor = equalized.astype(np.float32) / 255.0
    return tensor[np.newaxis, :, :, np.newaxis]
