"""Dobles de prueba importables por el proceso hijo de `IsolatedLungSegmenter`."""

from __future__ import annotations

import numpy as np

from neumonia.domain import LungMasks
from neumonia.model.lung_segmentation import geometric_masks


class FakePspnet:
    """Devuelve los rectángulos geométricos marcados como `pspnet` (para probar el canal)."""

    name = "pspnet"

    def segment(self, pixels: np.ndarray, size: int = 512) -> LungMasks:
        base = geometric_masks(size)
        return LungMasks(base.right, base.left, source="pspnet")


class ExplodingSegmenter:
    name = "pspnet"

    def segment(self, pixels: np.ndarray, size: int = 512) -> LungMasks:
        raise ValueError("imagen ilegible")


def broken_factory():
    raise ImportError("No module named 'torchxrayvision'")
