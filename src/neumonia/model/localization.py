"""Localización aproximada de la atención del modelo por zonas pulmonares.

Advertencias de diseño (ver ADR-0007):
- Grad-CAM indica **dónde miró el modelo**, no dónde está la lesión. El modelo no fue entrenado
  para segmentar ni localizar; estas cifras describen su atención, no la enfermedad.
- Las zonas salen de `LungMasks`: la silueta segmentada (PSPNet, ADR-0008) o, por defecto o como
  respaldo, una **aproximación geométrica** de los campos pulmonares. Cada pulmón se divide en
  tercios superior / medio / inferior según **su propia altura**.
- La alerta de atajo compara la **densidad** de atención (por píxel) fuera y dentro de los campos
  pulmonares: con atención uniforme la razón es 1.0; si es >= 1.0 el modelo mira tanto o más
  fuera de los pulmones (marcadores, bordes, dispositivos) que dentro.
- Convención radiológica: en una proyección PA/AP el **pulmón derecho del paciente aparece a la
  izquierda de la imagen**.
"""

from __future__ import annotations

import cv2
import numpy as np

from neumonia.config import IMG_SIZE
from neumonia.domain import ZONE_NAMES, Findings, LungMasks
from neumonia.model.lung_segmentation import geometric_masks

HIGH_ATTENTION = 0.5
SHORTCUT_DENSITY_RATIO = 1.0  # atención por píxel fuera >= dentro → sospecha de atajo
FOCUS_MIN = 0.15
LATERALITY_RATIO = 1.5
MAX_RATIO = 99.0  # tope de la razón cuando casi no hay atención dentro (JSON sin infinitos)


def upsample(cam: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    """Lleva el mapa de Grad-CAM (31×31) a la resolución de la imagen (size×size)."""
    resized = cv2.resize(np.asarray(cam, dtype=np.float32), (size, size))
    return np.clip(resized, 0.0, 1.0)


def zones_from_lungs(lungs: LungMasks) -> dict[str, np.ndarray]:
    """Seis máscaras disjuntas: cada pulmón partido en tercios de su propia altura."""
    masks: dict[str, np.ndarray] = {}
    for side, lung in (("derecho", lungs.right), ("izquierdo", lungs.left)):
        rows = np.nonzero(lung.any(axis=1))[0]
        bands = np.zeros(lung.shape[0], dtype=int) - 1
        if rows.size:
            edges = np.linspace(rows[0], rows[-1] + 1, 4).astype(int)
            for i in range(3):
                bands[edges[i] : edges[i + 1]] = i
        for i, level in enumerate(("superior", "medio", "inferior")):
            masks[f"{side}_{level}"] = lung & (bands == i)[:, None]
    return masks


def zone_masks(size: int = IMG_SIZE) -> dict[str, np.ndarray]:
    """Zonas geométricas de referencia (compatibilidad con la versión 0.4.0)."""
    return zones_from_lungs(geometric_masks(size))


def lung_field(size: int = IMG_SIZE) -> np.ndarray:
    return geometric_masks(size).lung_field


def classify_laterality(right: float, left: float) -> str:
    if max(right, left) < FOCUS_MIN:
        return "sin_foco"
    if right >= LATERALITY_RATIO * left:
        return "derecho"
    if left >= LATERALITY_RATIO * right:
        return "izquierdo"
    return "bilateral"


def _safe_mean(values: np.ndarray) -> float:
    return float(values.mean()) if values.size else 0.0


def analyze_attention(
    cam: np.ndarray, size: int = IMG_SIZE, lungs: LungMasks | None = None
) -> Findings:
    """Resume un mapa de Grad-CAM normalizado ([0, 1], cualquier resolución) por zonas.

    `lungs` son los campos pulmonares a `size`×`size`; si no se dan, se usan los geométricos.
    """
    raw = np.clip(np.nan_to_num(np.asarray(cam, dtype=np.float64)), 0.0, 1.0)
    lungs = lungs if lungs is not None else geometric_masks(size)
    size = lungs.right.shape[0]
    heat = upsample(raw, size).astype(np.float64)
    masks = zones_from_lungs(lungs)
    field = lungs.lung_field

    zone_attention = {name: _safe_mean(heat[masks[name]]) for name in ZONE_NAMES}
    total = float(heat.sum())
    out_of_lung_pct = 100.0 * float(heat[~field].sum()) / total if total > 0 else 0.0
    inside_density = _safe_mean(heat[field])
    outside_density = _safe_mean(heat[~field])
    ratio = 0.0 if total <= 0 else min(MAX_RATIO, outside_density / max(inside_density, 1e-09))
    extent_pct = 100.0 * _safe_mean(heat[field] >= HIGH_ATTENTION)

    # Zona más intensa de cada lado: un foco en una sola zona no se diluye con las otras dos.
    right = max(v for k, v in zone_attention.items() if k.startswith("derecho"))
    left = max(v for k, v in zone_attention.items() if k.startswith("izquierdo"))
    laterality = classify_laterality(right, left)
    dominant = max(zone_attention, key=zone_attention.get) if total > 0 else ""

    return Findings(
        zone_attention=zone_attention,
        dominant_zone=dominant,
        laterality=laterality,
        extent_pct=extent_pct,
        out_of_lung_pct=out_of_lung_pct,
        shortcut_warning=total > 0 and ratio >= SHORTCUT_DENSITY_RATIO,
        outside_inside_ratio=ratio,
        attention_grid=raw.tolist(),
        lung_source=lungs.source,
        lung_note=lungs.note,
        lung_grid=lungs.label_grid(),
    )
