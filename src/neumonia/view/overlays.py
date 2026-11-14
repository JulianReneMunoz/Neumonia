"""Superposición 2D de las zonas pulmonares usadas por el análisis (solo numpy, sin cv2).

Permite al médico comprobar a simple vista si la silueta segmentada (o los rectángulos
geométricos de respaldo) coincide con los pulmones de la radiografía.
"""

from __future__ import annotations

import numpy as np

OUT_SIZE = 384
LUNG_COLORS = {1: (52, 120, 246), 2: (34, 170, 90)}  # 1 = derecho (azul), 2 = izquierdo (verde)
DOMINANT_COLOR = (245, 140, 20)
TINT_ALPHA = 0.22
DOMINANT_ALPHA = 0.45


def _resample(image: np.ndarray, size: int) -> np.ndarray:
    rows = np.linspace(0, image.shape[0] - 1, size).astype(int)
    cols = np.linspace(0, image.shape[1] - 1, size).astype(int)
    return image[np.ix_(rows, cols)]


def _thirds(lung: np.ndarray) -> np.ndarray:
    """Índice de tercio (0, 1, 2) por fila según la altura del propio pulmón; -1 fuera."""
    bands = np.full(lung.shape[0], -1)
    rows = np.nonzero(lung.any(axis=1))[0]
    if rows.size:
        edges = np.linspace(rows[0], rows[-1] + 1, 4).astype(int)
        for i in range(3):
            bands[edges[i] : edges[i + 1]] = i
    return bands


def _boundary(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1)
    inner = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:] & mask
    return mask & ~inner


def zones_overlay(
    original_rgb: np.ndarray, lung_grid: list[list[int]], dominant_zone: str = ""
) -> np.ndarray:
    """Radiografía con cada pulmón coloreado, sus tercios marcados y la zona dominante resaltada."""
    grid = np.asarray(lung_grid, dtype=int)
    if grid.ndim != 2 or grid.size == 0:
        raise ValueError("lung_grid debe ser una matriz 2D no vacía.")
    base = np.asarray(original_rgb)
    if base.ndim == 2:
        base = np.repeat(base[..., None], 3, axis=2)
    out = _resample(base[..., :3], OUT_SIZE).astype(np.float64)
    labels = _resample(grid, OUT_SIZE)
    side_of = {"derecho": 1, "izquierdo": 2}
    levels = {"superior": 0, "medio": 1, "inferior": 2}
    dom_side, _, dom_level = dominant_zone.partition("_")
    for value, color in LUNG_COLORS.items():
        lung = labels == value
        if not lung.any():
            continue
        tint = np.asarray(color, dtype=np.float64)
        out[lung] = (1 - TINT_ALPHA) * out[lung] + TINT_ALPHA * tint
        bands = _thirds(lung)
        if side_of.get(dom_side) == value and dom_level in levels:
            dom = lung & (bands == levels[dom_level])[:, None]
            out[dom] = (1 - DOMINANT_ALPHA) * out[dom] + DOMINANT_ALPHA * np.asarray(
                DOMINANT_COLOR, dtype=np.float64
            )
        out[_boundary(lung)] = tint
        cuts = np.nonzero(np.diff(bands) != 0)[0] + 1
        for row in cuts:
            if 0 < row < OUT_SIZE and bands[row] > 0:
                out[row, lung[row]] = tint
    return np.clip(out, 0, 255).astype(np.uint8)
