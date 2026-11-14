"""Tres corridas comparables de inferencia para MLflow (SPEC-013).

El modelo no se entrena (MaaS): cada corrida evalúa la MISMA versión de conv_MLP_84 sobre el mismo
conjunto etiquetado y cambia una sola cosa: el umbral de decisión o el preprocesamiento. Se miden la
calidad (exactitud, precisión, sensibilidad, especificidad, F1, AUC) y el servicio (latencia media,
p95 y throughput). Este módulo no importa MLflow: devuelve diccionarios que el script registra.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from neumonia.config import CLASS_NAMES, IMG_SIZE, NORMAL_INDEX
from neumonia.evaluation import binary_metrics
from neumonia.model.preprocessing import preprocess, to_gray
from neumonia.model.readers import InvalidImageError, read_path

CLAHE_STEPS = "resize 512 + gris + CLAHE(2.0, 4x4) + [0,1]"
PLAIN_STEPS = "resize 512 + gris + [0,1] (sin CLAHE)"


@dataclass(frozen=True)
class RunConfig:
    name: str
    threshold: float
    clahe: bool
    description: str

    @property
    def preprocessing(self) -> str:
        return CLAHE_STEPS if self.clahe else PLAIN_STEPS


RUNS: tuple[RunConfig, ...] = (
    RunConfig(
        "baseline-umbral-0.50",
        0.5,
        True,
        "Línea base: preprocesamiento de entrenamiento y umbral por defecto.",
    ),
    RunConfig(
        "umbral-0.30",
        0.3,
        True,
        "Mismo modelo y preprocesamiento; umbral más sensible (menos falsos negativos).",
    ),
    RunConfig(
        "sin-clahe-umbral-0.50",
        0.5,
        False,
        "Sin CLAHE: mide el efecto de romper la paridad entrenamiento/servicio.",
    ),
)


@dataclass(frozen=True)
class LabeledImage:
    path: Path
    target: int  # 1 = neumonía, 0 = sin neumonía
    group: str = ""


@dataclass
class RunResult:
    config: RunConfig
    metrics: dict[str, float]
    rows: list[dict[str, Any]] = field(default_factory=list)
    skipped: int = 0


def preprocess_variant(pixels: np.ndarray, clahe: bool, size: int = IMG_SIZE) -> np.ndarray:
    """Tensor (1, size, size, 1) en [0, 1]; con CLAHE es idéntico a `preprocess`."""
    if clahe:
        return preprocess(pixels, size)
    gray = to_gray(cv2.resize(pixels, (size, size)))
    return (gray.astype(np.float32) / 255.0)[np.newaxis, :, :, np.newaxis]


def latency_summary(latencies_ms: Sequence[float]) -> dict[str, float]:
    """Latencia media, p50 y p95 (ms) y throughput (imágenes por segundo, en serie)."""
    if not latencies_ms:
        raise ValueError("No hay latencias que resumir.")
    values = np.asarray(latencies_ms, dtype=float)
    mean = float(values.mean())
    return {
        "latency_mean_ms": round(mean, 2),
        "latency_p50_ms": round(float(np.percentile(values, 50)), 2),
        "latency_p95_ms": round(float(np.percentile(values, 95)), 2),
        "throughput_img_s": round(1000.0 / mean, 3) if mean > 0 else 0.0,
    }


def label_from_course_path(path: Path) -> int | None:
    """Muestras del aula: la carpeta o el nombre dicen la clase (normal / bacteria / virus)."""
    text = path.as_posix().lower()
    if "normal" in text:
        return 0
    if any(word in text for word in ("bacteria", "virus", "viral")):
        return 1
    return None


def course_items(folder: Path) -> list[LabeledImage]:
    items = []
    for path in sorted(folder.rglob("*")):
        if path.suffix.lower() not in {".dcm", ".jpg", ".jpeg", ".png"}:
            continue
        target = label_from_course_path(path)
        if target is not None:
            items.append(LabeledImage(path, target, path.suffix.lower().lstrip(".")))
    return items


def sample_items(items: Sequence[LabeledImage], limit: int | None, seed: int) -> list[LabeledImage]:
    """Submuestra reproducible que conserva la proporción de clases."""
    chosen = list(items)
    if limit is None or limit >= len(chosen):
        return sorted(chosen, key=lambda i: str(i.path))
    rng = random.Random(seed)  # noqa: S311 - muestreo reproducible, no criptografía
    by_class: dict[int, list[LabeledImage]] = {}
    for item in sorted(chosen, key=lambda i: str(i.path)):
        by_class.setdefault(item.target, []).append(item)
    out: list[LabeledImage] = []
    for _target, group in sorted(by_class.items()):
        rng.shuffle(group)
        share = round(limit * len(group) / len(chosen))
        out.extend(group[: max(1, share)])
    return sorted(out[:limit], key=lambda i: str(i.path))


def run_config(
    predict_proba: Callable[[np.ndarray], np.ndarray],
    items: Iterable[LabeledImage],
    config: RunConfig,
    clock: Callable[[], float] = time.perf_counter,
    normal_index: int = NORMAL_INDEX,
) -> RunResult:
    """Corre una configuración: lee, preprocesa, infiere y mide calidad y latencia."""
    rows: list[dict[str, Any]] = []
    latencies: list[float] = []
    skipped = 0
    for item in items:
        try:
            image = read_path(item.path)
        except (InvalidImageError, FileNotFoundError):
            skipped += 1
            continue
        start = clock()
        probs = np.asarray(predict_proba(preprocess_variant(image.pixels, config.clahe)))
        latencies.append((clock() - start) * 1000.0)
        p_pneumonia = 1.0 - float(probs[normal_index])
        rows.append(
            {
                "image": item.path.name,
                "group": item.group,
                "target": item.target,
                "p_pneumonia": round(p_pneumonia, 6),
                "pred": int(p_pneumonia >= config.threshold),
                **{f"p_{n}": round(float(p), 6) for n, p in zip(CLASS_NAMES, probs, strict=True)},
            }
        )
    if not rows:
        raise ValueError("Ninguna imagen se pudo leer.")
    quality = binary_metrics(
        [r["target"] for r in rows], [r["p_pneumonia"] for r in rows], config.threshold
    )
    metrics = {k: float(v) for k, v in quality.items() if isinstance(v, int | float)}
    metrics.update(latency_summary(latencies))
    metrics["skipped"] = float(skipped)
    return RunResult(config, metrics, rows, skipped)


def confusion(rows: Sequence[dict[str, Any]]) -> list[list[int]]:
    """Matriz [[TN, FP], [FN, TP]] a partir de las filas de una corrida."""
    matrix = [[0, 0], [0, 0]]
    for row in rows:
        matrix[int(row["target"])][int(row["pred"])] += 1
    return matrix
