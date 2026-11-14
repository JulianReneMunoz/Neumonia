"""¿Grad-CAM mira donde está la lesión? Evaluación contra las cajas de RSNA (fase 2, ADR-0009).

Para cada radiografía con neumonía, RSNA trae 1–4 cajas de opacidad dibujadas por radiólogos.
Se compara el mapa Grad-CAM (31×31, llevado a 512×512 como la entrada del modelo) con la unión de
esas cajas usando tres métricas habituales para mapas de saliencia en radiografía de tórax:

- **Acierto del punto máximo** (*pointing game*): ¿la región de máxima atención (≥ 99 % del
  máximo; robusta a empates) cae mayoritariamente dentro de una caja?
  Línea base: la fracción de la imagen cubierta por cajas (lo que acertaría un punto al azar).
- **Energía dentro de las cajas**: fracción de la atención total que cae dentro de las cajas.
  Línea base: la misma fracción de área. `enriquecimiento = energía / área` (1.0 = como el azar).
- **IoU**: intersección sobre unión entre la región de alta atención (≥ 0.5) y las cajas.

No mide si el diagnóstico es correcto (eso lo hace `evaluation.py`), sino si la explicación apunta
a la lesión. Una explicación que apunta a marcadores o bordes ("atajo") da valores bajos.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from neumonia.config import IMG_SIZE
from neumonia.controller.service import PneumoniaService
from neumonia.model.localization import HIGH_ATTENTION, upsample
from neumonia.model.readers import InvalidImageError, read_path
from neumonia.tracking.tracker import Tracker

PEAK_FRACTION = 0.99


@dataclass(frozen=True)
class Box:
    """Caja de opacidad de RSNA en píxeles de la imagen original (esquina superior izquierda)."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class LocalizationCase:
    patient_id: str
    image_path: str
    boxes: list[Box] = field(default_factory=list)


ID_COLUMNS = ("patientId", "SOPInstanceUID", "sop_instance_uid", "StudyInstanceUID", "image_id")
SIZE_COLUMNS = {"width": ("width", "w"), "height": ("height", "h")}


def _column(fieldnames: list[str], options: tuple[str, ...], what: str) -> str:
    lowered = {name.lower(): name for name in fieldnames}
    for option in options:
        if option.lower() in lowered:
            return lowered[option.lower()]
    raise ValueError(f"El CSV no tiene columna de {what} (se buscó {', '.join(options)}).")


def load_rsna_boxes(labels_csv: Path) -> dict[str, list[Box]]:
    """Cajas por imagen. Acepta dos formatos de RSNA 2018:

    - Kaggle `stage_2_train_labels.csv`: patientId, x, y, width, height, Target.
    - Exportación adjudicada (MD.ai) convertida a CSV, p. ej. `rsna_boxes.csv`, con SOPInstanceUID
      como clave y una fila por caja (sin columna Target).
    """
    boxes: dict[str, list[Box]] = defaultdict(list)
    with Path(labels_csv).open(encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        id_col = _column(fields, ID_COLUMNS, "identificador")
        x_col = _column(fields, ("x",), "x")
        y_col = _column(fields, ("y",), "y")
        w_col = _column(fields, SIZE_COLUMNS["width"], "ancho")
        h_col = _column(fields, SIZE_COLUMNS["height"], "alto")
        target_col = next((f for f in fields if f.lower() == "target"), None)
        for row in reader:
            if target_col and int(float(row[target_col] or 0)) != 1:
                continue
            if not row.get(x_col):
                continue
            boxes[row[id_col]].append(
                Box(float(row[x_col]), float(row[y_col]), float(row[w_col]), float(row[h_col]))
            )
    return dict(boxes)


def index_dicoms(images_dir: Path) -> dict[str, Path]:
    """Nombre del archivo sin extensión → ruta, buscando en subcarpetas (estructura de cada zip)."""
    return {path.stem: path for path in Path(images_dir).rglob("*.dcm")}


def build_cases(
    labels_csv: Path, images_dir: Path, limit: int | None = None, seed: int = 42
) -> list[LocalizationCase]:
    """Casos con cajas cuya imagen existe, en orden aleatorio reproducible."""
    by_image = load_rsna_boxes(labels_csv)
    files = index_dicoms(images_dir)
    cases = [
        LocalizationCase(key, str(files[key]), boxes)
        for key, boxes in sorted(by_image.items())
        if key in files
    ]
    random.Random(seed).shuffle(cases)  # noqa: S311 - muestreo reproducible, no criptografía
    return cases[:limit] if limit is not None else cases


def boxes_mask(boxes: Iterable[Box], rows: int, cols: int, size: int = IMG_SIZE) -> np.ndarray:
    """Unión de las cajas, reescalada de la imagen original (rows×cols) a size×size."""
    mask = np.zeros((size, size), dtype=bool)
    sy, sx = size / rows, size / cols
    for box in boxes:
        r0 = max(0, math.floor(box.y * sy))
        r1 = min(size, math.ceil((box.y + box.height) * sy))
        c0 = max(0, math.floor(box.x * sx))
        c1 = min(size, math.ceil((box.x + box.width) * sx))
        mask[r0:r1, c0:c1] = True
    return mask


def localization_scores(cam: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    """Métricas de un caso. `cam` en [0, 1] a cualquier resolución; `mask` define el tamaño."""
    size = mask.shape[0]
    heat = upsample(np.clip(np.nan_to_num(np.asarray(cam, dtype=np.float64)), 0, 1), size)
    heat = heat.astype(np.float64)
    area = float(mask.mean())
    total = float(heat.sum())
    if total <= 0 or area == 0:
        return {"hit": 0.0, "energy_in": 0.0, "area_fraction": area, "enrichment": 0.0, "iou": 0.0}
    peak = heat >= PEAK_FRACTION * float(heat.max())  # región del máximo: robusta a empates
    energy = float(heat[mask].sum()) / total
    high = heat >= HIGH_ATTENTION
    union = float((high | mask).sum())
    return {
        "hit": float(mask[peak].mean() >= 0.5),
        "energy_in": energy,
        "area_fraction": area,
        "enrichment": energy / area,
        "iou": float((high & mask).sum()) / union if union else 0.0,
    }


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC 95 % de Wilson para una proporción (estable con n pequeño)."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Promedios globales y del subconjunto que el modelo sí clasificó como neumonía."""
    summary: dict[str, float] = {"n": float(len(rows))}
    if not rows:
        return summary
    for prefix, subset in (("", rows), ("tp_", [r for r in rows if r["label"] == "PNEUMONIA"])):
        if not subset:
            continue
        hits = int(sum(r["hit"] for r in subset))
        low, high = wilson_interval(hits, len(subset))
        summary.update(
            {
                f"{prefix}n": float(len(subset)),
                f"{prefix}pointing_hit_rate": hits / len(subset),
                f"{prefix}pointing_ci_low": low,
                f"{prefix}pointing_ci_high": high,
                f"{prefix}pointing_baseline": float(np.mean([r["area_fraction"] for r in subset])),
                f"{prefix}energy_in_mean": float(np.mean([r["energy_in"] for r in subset])),
                f"{prefix}enrichment_mean": float(np.mean([r["enrichment"] for r in subset])),
                f"{prefix}iou_mean": float(np.mean([r["iou"] for r in subset])),
                f"{prefix}shortcut_rate": float(np.mean([r["shortcut_warning"] for r in subset])),
            }
        )
    return summary


@dataclass
class LocalizationResult:
    summary: dict[str, float]
    rows: list[dict[str, Any]]
    skipped: int


def evaluate_localization(
    service: PneumoniaService,
    cases: list[LocalizationCase],
    tracker: Tracker,
    out_dir: Path,
    params: dict[str, Any] | None = None,
) -> LocalizationResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    skipped = 0
    with tracker.run(run_name="evaluate_localization"):
        tracker.log_params({"n_cases": len(cases), **(params or {})})
        for case in cases:
            try:
                image = read_path(case.image_path)
            except (InvalidImageError, OSError):
                skipped += 1
                continue
            prediction = service.predict_image(image)
            findings = prediction.findings
            if findings is None or not findings.attention_grid:
                skipped += 1
                continue
            rows_px, cols_px = image.pixels.shape[:2]
            mask = boxes_mask(case.boxes, rows_px, cols_px)
            scores = localization_scores(np.asarray(findings.attention_grid), mask)
            rows.append(
                {
                    "case_id": case.patient_id,  # UID público y anonimizado de RSNA
                    "n_boxes": len(case.boxes),
                    "label": prediction.label.value,
                    "probability": round(prediction.probability, 4),
                    "shortcut_warning": int(findings.shortcut_warning),
                    "lung_source": findings.lung_source,
                    **{k: round(v, 4) for k, v in scores.items()},
                }
            )
        summary = summarize(rows)
        tracker.log_metrics({k: v for k, v in summary.items() if k != "n"})
        per_case = out_dir / "localizacion_por_caso.csv"
        if rows:
            with per_case.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            tracker.log_artifact(per_case)
        report = out_dir / "localizacion_resumen.json"
        report.write_text(
            json.dumps({"summary": summary, "skipped": skipped}, indent=2), encoding="utf-8"
        )
        tracker.log_artifact(report)
    return LocalizationResult(summary=summary, rows=rows, skipped=skipped)
