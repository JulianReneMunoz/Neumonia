"""Localización aproximada de la atención del modelo por zonas pulmonares.

Advertencias de diseño (ver ADR-0007):
- Grad-CAM indica **dónde miró el modelo**, no dónde está la lesión. El modelo no fue entrenado
  para segmentar ni localizar; estas cifras describen su atención, no la enfermedad.
- Las zonas son una **aproximación geométrica** de los campos pulmonares en una radiografía frontal
  estándar (sin segmentación pulmonar). Imágenes rotadas o recortadas reducen su exactitud.
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
from neumonia.domain import ZONE_NAMES, Findings

# Campos pulmonares aproximados como fracción del ancho/alto de la imagen.
TOP, BOTTOM = 0.12, 0.88
RIGHT_LUNG_X = (0.08, 0.47)  # mitad izquierda de la imagen = pulmón derecho del paciente
LEFT_LUNG_X = (0.53, 0.92)
HIGH_ATTENTION = 0.5
SHORTCUT_DENSITY_RATIO = 1.0  # atención por píxel fuera >= dentro → sospecha de atajo
FOCUS_MIN = 0.15
LATERALITY_RATIO = 1.5
MAX_RATIO = 99.0  # tope de la razón cuando casi no hay atención dentro (JSON sin infinitos)


def upsample(cam: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    """Lleva el mapa de Grad-CAM (31×31) a la resolución de la imagen (size×size)."""
    resized = cv2.resize(np.asarray(cam, dtype=np.float32), (size, size))
    return np.clip(resized, 0.0, 1.0)


def zone_masks(size: int = IMG_SIZE) -> dict[str, np.ndarray]:
    """Seis máscaras booleanas (derecho/izquierdo × superior/medio/inferior)."""
    masks: dict[str, np.ndarray] = {}
    rows = np.linspace(TOP, BOTTOM, 4) * size
    for side, (x0, x1) in (("derecho", RIGHT_LUNG_X), ("izquierdo", LEFT_LUNG_X)):
        c0, c1 = int(x0 * size), int(x1 * size)
        for i, level in enumerate(("superior", "medio", "inferior")):
            r0, r1 = int(rows[i]), int(rows[i + 1])
            mask = np.zeros((size, size), dtype=bool)
            mask[r0:r1, c0:c1] = True
            masks[f"{side}_{level}"] = mask
    return masks


def lung_field(size: int = IMG_SIZE) -> np.ndarray:
    union = np.zeros((size, size), dtype=bool)
    for mask in zone_masks(size).values():
        union |= mask
    return union


def classify_laterality(right: float, left: float) -> str:
    if max(right, left) < FOCUS_MIN:
        return "sin_foco"
    if right >= LATERALITY_RATIO * left:
        return "derecho"
    if left >= LATERALITY_RATIO * right:
        return "izquierdo"
    return "bilateral"


def analyze_attention(cam: np.ndarray, size: int = IMG_SIZE) -> Findings:
    """Resume un mapa de Grad-CAM normalizado ([0, 1], cualquier resolución) por zonas."""
    raw = np.clip(np.nan_to_num(np.asarray(cam, dtype=np.float64)), 0.0, 1.0)
    heat = upsample(raw, size).astype(np.float64)
    masks = zone_masks(size)
    field = lung_field(size)

    zone_attention = {name: float(heat[masks[name]].mean()) for name in ZONE_NAMES}
    total = float(heat.sum())
    out_of_lung_pct = 100.0 * float(heat[~field].sum()) / total if total > 0 else 0.0
    inside_density = float(heat[field].mean())
    outside_density = float(heat[~field].mean())
    ratio = 0.0 if total <= 0 else min(MAX_RATIO, outside_density / max(inside_density, 1e-09))
    extent_pct = 100.0 * float((heat[field] >= HIGH_ATTENTION).mean())

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
    )
