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


ZONE_NAMES: tuple[str, ...] = (
    "derecho_superior",
    "derecho_medio",
    "derecho_inferior",
    "izquierdo_superior",
    "izquierdo_medio",
    "izquierdo_inferior",
)


@dataclass(frozen=True)
class Findings:
    """Hallazgos derivados del mapa de atención (Grad-CAM) — NO es una segmentación de lesiones.

    Describe **dónde miró el modelo**: atención media por zona pulmonar aproximada, lateralidad,
    extensión de la región de alta atención dentro de los campos pulmonares y la fracción de
    atención que cae fuera de ellos (indicador de posible aprendizaje por atajos).
    """

    zone_attention: dict[str, float]
    dominant_zone: str
    laterality: str  # derecho | izquierdo | bilateral | sin_foco
    extent_pct: float  # % del área pulmonar aproximada con atención >= 0.5
    out_of_lung_pct: float  # % de la atención total que cae fuera de los campos pulmonares
    shortcut_warning: bool
    attention_grid: list[list[float]]  # Grad-CAM a su resolución nativa (31×31), en [0, 1]
    outside_inside_ratio: float = 0.0  # densidad de atención fuera / dentro (1.0 = uniforme)
    summary: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_attention": {k: round(float(v), 4) for k, v in self.zone_attention.items()},
            "dominant_zone": self.dominant_zone,
            "laterality": self.laterality,
            "extent_pct": round(float(self.extent_pct), 2),
            "out_of_lung_pct": round(float(self.out_of_lung_pct), 2),
            "shortcut_warning": bool(self.shortcut_warning),
            "outside_inside_ratio": round(float(self.outside_inside_ratio), 3),
            "attention_grid": [[round(float(v), 3) for v in row] for row in self.attention_grid],
            "summary": list(self.summary),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Findings:
        return cls(
            zone_attention={k: float(v) for k, v in data.get("zone_attention", {}).items()},
            dominant_zone=str(data.get("dominant_zone", "")),
            laterality=str(data.get("laterality", "sin_foco")),
            extent_pct=float(data.get("extent_pct", 0.0)),
            out_of_lung_pct=float(data.get("out_of_lung_pct", 0.0)),
            shortcut_warning=bool(data.get("shortcut_warning", False)),
            outside_inside_ratio=float(data.get("outside_inside_ratio", 0.0)),
            attention_grid=[[float(v) for v in row] for row in data.get("attention_grid", [])],
            summary=[str(s) for s in data.get("summary", [])],
        )


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
    findings: Findings | None = None

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
            "findings": self.findings.to_dict() if self.findings is not None else None,
        }
