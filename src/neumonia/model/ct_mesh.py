"""Mallas 3D (marching cubes) y volúmenes reducidos para la vista de tomografía (ADR-0010).

Se calculan una vez y se guardan en caché (`ct_cache.py`): la vista solo dibuja triángulos, por eso
la demo carga al instante aunque la segmentación haya tardado minutos.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from neumonia.model.ct_segmentation import STRUCTURES, CtSegmentation

MAX_MESH_DIM = 128  # lado máximo de la rejilla usada para las mallas
LUNG_WINDOW = (-1350.0, 150.0)  # ventana pulmonar (W 1500, L -600)
LABEL_LUNG, LABEL_GGO, LABEL_CONSOLIDATION = 1, 2, 3


@dataclass(frozen=True)
class Mesh:
    vertices: np.ndarray  # (n, 3) float32 en mm
    faces: np.ndarray  # (m, 3) int32

    @property
    def empty(self) -> bool:
        return len(self.faces) == 0


def reduction_factor(shape: tuple[int, ...], max_dim: int = MAX_MESH_DIM) -> int:
    return max(1, int(np.ceil(max(shape) / max_dim)))


def downsample_mask(mask: np.ndarray, factor: int) -> np.ndarray:
    """Reduce por bloques: un bloque es verdadero si al menos la mitad lo es (sin cv2/scipy)."""
    if factor == 1:
        return mask.astype(bool)
    shape = tuple(dim // factor * factor for dim in mask.shape)
    trimmed = mask[: shape[0], : shape[1], : shape[2]].astype(np.float32)
    blocks = trimmed.reshape(
        shape[0] // factor, factor, shape[1] // factor, factor, shape[2] // factor, factor
    )
    return blocks.mean(axis=(1, 3, 5)) >= 0.5


def mask_to_mesh(mask: np.ndarray, spacing: tuple[float, float, float]) -> Mesh:
    from skimage.measure import marching_cubes

    if mask.sum() < 8:
        return Mesh(np.zeros((0, 3), np.float32), np.zeros((0, 3), np.int32))
    padded = np.pad(mask.astype(np.float32), 1)
    vertices, faces, _, _ = marching_cubes(padded, level=0.5, spacing=spacing)
    vertices -= np.asarray(spacing, dtype=np.float64)  # deshace el relleno
    return Mesh(vertices.astype(np.float32), faces.astype(np.int32))


def build_meshes(seg: CtSegmentation, max_dim: int = MAX_MESH_DIM) -> dict[str, Mesh]:
    factor = reduction_factor(seg.shape, max_dim)
    spacing = tuple(s * factor for s in seg.spacing)
    return {
        name: mask_to_mesh(downsample_mask(seg.masks[name], factor), spacing) for name in STRUCTURES
    }


def window_ct(ct: np.ndarray, window: tuple[float, float] = LUNG_WINDOW) -> np.ndarray:
    low, high = window
    scaled = (np.clip(ct.astype(np.float32), low, high) - low) / (high - low)
    return (scaled * 255).astype(np.uint8)


def slice_volumes(
    seg: CtSegmentation, max_dim: int = 192
) -> tuple[np.ndarray | None, np.ndarray, tuple[float, float, float]]:
    """Tomografía en ventana pulmonar (uint8) y etiquetas (0 fondo, 1 pulmón, 2 GGO, 3 consol.)."""
    factor = reduction_factor(seg.shape, max_dim)
    labels = np.zeros(seg.shape, dtype=np.uint8)
    labels[seg.masks["pulmon_derecho"] | seg.masks["pulmon_izquierdo"]] = LABEL_LUNG
    labels[seg.masks["vidrio_esmerilado"]] = LABEL_GGO
    labels[seg.masks["consolidacion"]] = LABEL_CONSOLIDATION
    labels = labels[::factor, ::factor, ::factor]
    ct = window_ct(seg.ct[::factor, ::factor, ::factor]) if seg.ct is not None else None
    spacing = tuple(s * factor for s in seg.spacing)
    return ct, labels, spacing
