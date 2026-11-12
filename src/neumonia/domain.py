"""Entidades del dominio. No dependen de TensorFlow, OpenCV ni de la web."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np


class Label(StrEnum):
    """Etiqueta binaria del contrato público (`label`)."""

    NORMAL = "NORMAL"
    PNEUMONIA = "PNEUMONIA"


@dataclass(frozen=True)
class RadiographImage:
    """Radiografía leída y normalizada a uint8 (H, W, 3), más metadatos no sensibles."""

    pixels: np.ndarray
    source_format: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.pixels.dtype != np.uint8 or self.pixels.ndim != 3 or self.pixels.shape[2] != 3:
            raise ValueError("pixels debe ser un arreglo uint8 de forma (H, W, 3).")


@dataclass(frozen=True)
class Prediction:
    """Resultado de una inferencia.

    - `label` / `probability`: decisión binaria del contrato (NORMAL | PNEUMONIA).
    - `subtype`: clase original del modelo de 3 salidas (bacteriana | normal | viral).
    - `class_probabilities`: salida softmax completa, para trazabilidad.
    - `heatmap`: imagen RGB uint8 512×512 con el Grad-CAM superpuesto (opcional).
    """

    label: Label
    probability: float
    subtype: str
    class_probabilities: dict[str, float]
    heatmap: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_contract(self, gradcam_url: str | None, model_version: str) -> dict[str, Any]:
        """Serializa al contrato de `api/openapi.yaml` (sin rutas locales ni datos sensibles)."""
        return {
            "label": self.label.value,
            "probability": round(float(self.probability), 4),
            "gradcam_url": gradcam_url,
            "subtype": self.subtype,
            "class_probabilities": {
                k: round(float(v), 4) for k, v in self.class_probabilities.items()
            },
            "metadata": dict(self.metadata),
            "model_version": model_version,
        }
