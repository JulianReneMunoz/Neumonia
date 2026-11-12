"""Evaluación del modelo (CRISP-DM fase 5) con métricas globales y por subgrupo.

Las métricas por subgrupo (sexo, edad, proyección AP/PA) usan los metadatos DICOM del
RSNA: permiten detectar sesgos, requisito de la gestión de riesgos del EU AI Act para
sistemas de alto riesgo (dispositivos médicos).
"""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from neumonia.controller.report import png_bytes
from neumonia.controller.service import PneumoniaService
from neumonia.data.dataset import Sample
from neumonia.model.metadata import age_group
from neumonia.model.readers import InvalidImageError, read_path
from neumonia.tracking.tracker import Tracker


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    """AUC por el estadístico de Mann-Whitney (maneja empates). None si hay una sola clase."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(len(y_score), dtype=float)
    sorted_scores = y_score[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def binary_metrics(
    y_true: Iterable[int], y_score: Iterable[float], threshold: float = 0.5
) -> dict[str, Any]:
    y_true = np.asarray(list(y_true), dtype=int)
    y_score = np.asarray(list(y_score), dtype=float)
    if y_true.shape != y_score.shape:
        raise ValueError("y_true y y_score deben tener la misma longitud.")
    y_pred = (y_score >= threshold).astype(int)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    def ratio(a: int, b: int) -> float | None:
        return a / b if b else None

    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return {
        "n": len(y_true),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": ratio(tp + tn, len(y_true)),
        "precision": precision,
        "recall": recall,  # sensibilidad
        "specificity": ratio(tn, tn + fp),
        "f1": f1,
        "roc_auc": roc_auc(y_true, y_score),
    }


def subgroup_metrics(
    rows: list[dict[str, Any]], key: str, threshold: float = 0.5
) -> dict[str, dict]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key) or "desconocido")].append(row)
    return {
        name: binary_metrics(
            [r["target"] for r in items], [r["p_pneumonia"] for r in items], threshold
        )
        for name, items in sorted(groups.items())
    }


@dataclass
class EvaluationResult:
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    subgroups: dict[str, dict[str, dict]]
    skipped: int


def evaluate(
    service: PneumoniaService,
    samples: list[Sample],
    tracker: Tracker,
    out_dir: Path,
    params: dict[str, Any] | None = None,
    gradcam_examples: int = 4,
) -> EvaluationResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    threshold = getattr(service.policy, "threshold", 0.5)
    rows: list[dict[str, Any]] = []
    skipped = 0
    start = time.perf_counter()
    with tracker.run(run_name="evaluate"):
        tracker.log_params({"threshold": threshold, "n_samples": len(samples), **(params or {})})
        for idx, sample in enumerate(samples):
            try:
                image = read_path(sample.image_path)
            except (InvalidImageError, FileNotFoundError):
                skipped += 1
                continue
            prediction = service.predict_image(image, explain=idx < gradcam_examples)
            p_normal = prediction.class_probabilities.get("normal", 0.0)
            meta = {**sample.metadata, **image.metadata}
            rows.append(
                {
                    "image": Path(sample.image_path).name,
                    "target": sample.target,
                    "p_pneumonia": round(1.0 - p_normal, 6),
                    "label": prediction.label.value,
                    "subtype_pred": prediction.subtype,
                    "subtype_true": sample.subtype,
                    "sex": meta.get("sex", ""),
                    "age_group": age_group(meta.get("age")),
                    "view_position": meta.get("view_position", ""),
                }
            )
            if prediction.heatmap is not None:
                example = out_dir / f"gradcam_{idx:03d}_{Path(sample.image_path).stem}.png"
                example.write_bytes(png_bytes(prediction.heatmap))
                tracker.log_artifact(example)

        metrics = binary_metrics(
            [r["target"] for r in rows], [r["p_pneumonia"] for r in rows], threshold
        )
        subgroups = {
            key: subgroup_metrics(rows, key, threshold)
            for key in ("sex", "age_group", "view_position")
        }
        elapsed = time.perf_counter() - start
        flat = {k: v for k, v in metrics.items() if isinstance(v, int | float)}
        flat["seconds_per_image"] = elapsed / max(1, len(rows))
        flat["skipped"] = skipped
        for key, groups in subgroups.items():
            for name, values in groups.items():
                if values["recall"] is not None:
                    flat[f"recall__{key}__{name}"] = values["recall"]
        tracker.log_metrics(flat)

        predictions_csv = out_dir / "predictions.csv"
        with predictions_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["image"])
            writer.writeheader()
            writer.writerows(rows)
        report = out_dir / "metrics.json"
        report.write_text(
            json.dumps({"global": metrics, "subgroups": subgroups, "skipped": skipped}, indent=2),
            encoding="utf-8",
        )
        tracker.log_artifact(predictions_csv)
        tracker.log_artifact(report)
    return EvaluationResult(rows, metrics, subgroups, skipped)
