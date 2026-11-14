"""Orquesta el prototipo de tomografía: segmentar → analizar → mallas → caché (ADR-0010).

La vista solo pide casos ya procesados (`load`); el procesamiento pesado (`process`) se hace antes,
con `make ct-precompute`, porque MEDPSeg tarda minutos por tomografía en CPU.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from neumonia.config import Settings
from neumonia.controller.ct_analysis import CtReport, analyze
from neumonia.model.ct_cache import CachedCase, list_cases, load_case, save_case
from neumonia.model.ct_mesh import build_meshes, slice_volumes
from neumonia.model.ct_segmentation import CtSegmentation, MedpsegSegmenter


class CtSegmenter(Protocol):
    def segment(self, ct_path: Path, out_dir: Path) -> CtSegmentation: ...


def cache_segmentation(seg: CtSegmentation, cache_dir: Path) -> Path:
    """Analiza una segmentación ya hecha y la guarda lista para la vista."""
    report = analyze(seg)
    ct, labels, spacing = slice_volumes(seg)
    return save_case(
        Path(cache_dir) / f"{seg.case_id}.npz",
        seg.case_id,
        build_meshes(seg),
        report.to_dict(),
        labels,
        spacing,
        ct,
    )


def process(ct_path: Path, segmenter: CtSegmenter, work_dir: Path, cache_dir: Path) -> Path:
    case_id = Path(ct_path).name.replace(".nii.gz", "").replace(".nii", "")
    seg = segmenter.segment(Path(ct_path), Path(work_dir) / case_id)
    return cache_segmentation(seg, cache_dir)


def build_ct_segmenter(settings: Settings) -> CtSegmenter | None:
    """MEDPSeg si su entorno está configurado (`NEUMONIA_MEDPSEG_PYTHON`); si no, None."""
    if settings.medpseg_python is None:
        return None
    return MedpsegSegmenter(settings.medpseg_python)


def available_cases(cache_dir: Path) -> dict[str, Path]:
    return {path.stem: path for path in list_cases(cache_dir)}


def load(path: Path) -> tuple[CachedCase, CtReport]:
    case = load_case(path)
    return case, CtReport.from_dict(case.report)
