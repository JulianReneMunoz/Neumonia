"""Informe cuantitativo de la tomografía (prototipo, ADR-0010).

A partir de las máscaras de MEDPSeg calcula volúmenes, el porcentaje de cada pulmón y de cada
lóbulo comprometido por lesión (vidrio esmerilado + consolidación) y el **puntaje de severidad
tomográfica** semicuantitativo por lóbulo (0–5 cada uno, 0–25 total): 0 sin compromiso,
1 < 5 %, 2 5–25 %, 3 26–50 %, 4 51–75 %, 5 > 75 %.

Umbral de ruido: la segmentación automática marca densidades mínimas incluso en pulmones sanos
(≈ 0.1–0.4 % por lóbulo en la tomografía de prueba). Un lóbulo con menos del 1 % puntúa 0; sin
este umbral, un tórax sano sumaría 5/25.

Es un prototipo de investigación sin validación clínica: el informe lo dice siempre.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from neumonia.model.ct_segmentation import CtSegmentation

# Etiquetas de lóbulo de MEDPSeg (pipeline.py: ["LUL", "LLL", "RUL", "RML", "RLL"]).
LOBES = {
    1: "lobulo_superior_izquierdo",
    2: "lobulo_inferior_izquierdo",
    3: "lobulo_superior_derecho",
    4: "lobulo_medio_derecho",
    5: "lobulo_inferior_derecho",
}
LOBE_LABELS = {
    "lobulo_superior_derecho": "Lóbulo superior derecho",
    "lobulo_medio_derecho": "Lóbulo medio derecho",
    "lobulo_inferior_derecho": "Lóbulo inferior derecho",
    "lobulo_superior_izquierdo": "Lóbulo superior izquierdo",
    "lobulo_inferior_izquierdo": "Lóbulo inferior izquierdo",
}
NOISE_FLOOR_PERCENT = 1.0
NOTE = (
    "Prototipo de investigación: segmentación automática (MEDPSeg) sin validación clínica local. "
    "No reemplaza la lectura de un radiólogo."
)


def lobe_severity(percent: float) -> int:
    """Puntaje 0–5 de un lóbulo según su porcentaje comprometido."""
    if percent < NOISE_FLOOR_PERCENT:
        return 0
    if percent < 5:
        return 1
    if percent <= 25:
        return 2
    if percent <= 50:
        return 3
    if percent <= 75:
        return 4
    return 5


def _percent(part: np.ndarray, whole: np.ndarray) -> float:
    total = int(whole.sum())
    return 100.0 * int((part & whole).sum()) / total if total else 0.0


@dataclass(frozen=True)
class LobeFinding:
    name: str
    volume_ml: float
    percent: float
    score: int


@dataclass(frozen=True)
class CtReport:
    case_id: str
    lung_volume_ml: dict[str, float]
    lesion_ml: float
    ggo_ml: float
    consolidation_ml: float
    percent_total: float
    percent_by_lung: dict[str, float]
    lobes: list[LobeFinding] = field(default_factory=list)
    severity_score: int | None = None  # 0–25, None si no hay lóbulos
    summary: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CtReport:
        data = dict(data)
        data["lobes"] = [LobeFinding(**lobe) for lobe in data.get("lobes", [])]
        return cls(**data)


def describe(report: CtReport) -> list[str]:
    lines: list[str] = []
    if report.lesion_ml <= 0:
        lines.append("No se segmentaron lesiones pulmonares (vidrio esmerilado ni consolidación).")
    elif report.percent_total < NOISE_FLOOR_PERCENT:
        lines.append(
            f"Hallazgos mínimos ({report.lesion_ml:.0f} mL, "
            f"{report.percent_total:.2f} % del pulmón), por debajo del umbral de ruido del "
            f"{NOISE_FLOOR_PERCENT:.0f} %: sin compromiso significativo."
        )
    else:
        right = report.percent_by_lung.get("pulmon_derecho", 0.0)
        left = report.percent_by_lung.get("pulmon_izquierdo", 0.0)
        side = (
            "bilateral" if min(right, left) >= 1 else ("derecho" if right > left else "izquierdo")
        )
        lines.append(
            f"Lesión segmentada de {report.lesion_ml:.0f} mL ({report.percent_total:.1f} % del "
            f"volumen pulmonar), con predominio {side}: pulmón derecho {right:.1f} %, "
            f"izquierdo {left:.1f} %."
        )
        lines.append(
            f"Vidrio esmerilado {report.ggo_ml:.0f} mL · consolidación "
            f"{report.consolidation_ml:.0f} mL."
        )
    if report.lobes:
        worst = max(report.lobes, key=lambda lobe: lobe.percent)
        if worst.percent >= NOISE_FLOOR_PERCENT:
            lines.append(
                f"Lóbulo más comprometido: {LOBE_LABELS.get(worst.name, worst.name).lower()} "
                f"({worst.percent:.1f} %)."
            )
        lines.append(f"Puntaje de severidad tomográfica: {report.severity_score}/25.")
    lines.append(NOTE)
    return lines


def analyze(seg: CtSegmentation) -> CtReport:
    right, left = seg.masks["pulmon_derecho"], seg.masks["pulmon_izquierdo"]
    lungs = right | left
    lesion = seg.lesion & lungs
    ggo = seg.masks["vidrio_esmerilado"] & lungs
    consolidation = seg.masks["consolidacion"] & lungs
    ml = seg.voxel_ml
    lobes: list[LobeFinding] = []
    if seg.lobes is not None:
        for label, name in LOBES.items():
            lobe = seg.lobes == label
            if lobe.any():
                percent = _percent(lesion, lobe)
                lobes.append(
                    LobeFinding(
                        name,
                        round(float(lobe.sum() * ml), 1),
                        round(percent, 2),
                        lobe_severity(percent),
                    )
                )
        order = list(LOBE_LABELS)
        lobes.sort(key=lambda lobe: order.index(lobe.name))
    report = CtReport(
        case_id=seg.case_id,
        lung_volume_ml={
            "pulmon_derecho": round(float(right.sum() * ml), 1),
            "pulmon_izquierdo": round(float(left.sum() * ml), 1),
        },
        lesion_ml=round(float(lesion.sum() * ml), 1),
        ggo_ml=round(float(ggo.sum() * ml), 1),
        consolidation_ml=round(float(consolidation.sum() * ml), 1),
        percent_total=round(_percent(lesion, lungs), 2),
        percent_by_lung={
            "pulmon_derecho": round(_percent(lesion, right), 2),
            "pulmon_izquierdo": round(_percent(lesion, left), 2),
        },
        lobes=lobes,
        severity_score=sum(lobe.score for lobe in lobes) if lobes else None,
    )
    return CtReport(**{**asdict(report), "lobes": lobes, "summary": describe(report)})
