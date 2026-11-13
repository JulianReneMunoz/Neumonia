"""Caché de casos de tomografía ya procesados (ADR-0010).

Un caso = mallas 3D + informe (JSON) + cortes reducidos con sus etiquetas, en un solo `.npz`
comprimido de pocos MB. Permite la demo en vivo sin MEDPSeg ni GPU: la segmentación (minutos en
CPU) se hace antes con `make ct-precompute`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from neumonia.model.ct_mesh import Mesh

CACHE_VERSION = 1


@dataclass(frozen=True)
class CachedCase:
    case_id: str
    meshes: dict[str, Mesh]
    report: dict[str, Any]
    labels: np.ndarray  # (x, y, z) uint8: 0 fondo, 1 pulmón, 2 vidrio esmerilado, 3 consolidación
    slice_spacing: tuple[float, float, float]
    ct: np.ndarray | None = None  # (x, y, z) uint8 en ventana pulmonar


def save_case(
    path: Path,
    case_id: str,
    meshes: dict[str, Mesh],
    report: dict[str, Any],
    labels: np.ndarray,
    slice_spacing: tuple[float, float, float],
    ct: np.ndarray | None = None,
) -> Path:
    arrays: dict[str, np.ndarray] = {
        "meta": np.frombuffer(
            json.dumps(
                {
                    "version": CACHE_VERSION,
                    "case_id": case_id,
                    "report": report,
                    "slice_spacing": list(slice_spacing),
                    "structures": list(meshes),
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            dtype=np.uint8,
        ),
        "labels": labels.astype(np.uint8),
    }
    if ct is not None:
        arrays["ct"] = ct.astype(np.uint8)
    for name, mesh in meshes.items():
        arrays[f"v_{name}"] = mesh.vertices.astype(np.float32)
        arrays[f"f_{name}"] = mesh.faces.astype(np.int32)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    return path


def load_case(path: Path) -> CachedCase:
    with np.load(Path(path), allow_pickle=False) as data:
        meta = json.loads(bytes(data["meta"]).decode("utf-8"))
        if meta.get("version") != CACHE_VERSION:
            raise ValueError(f"Versión de caché no soportada: {meta.get('version')}")
        meshes = {name: Mesh(data[f"v_{name}"], data[f"f_{name}"]) for name in meta["structures"]}
        return CachedCase(
            case_id=meta["case_id"],
            meshes=meshes,
            report=meta["report"],
            labels=data["labels"],
            slice_spacing=tuple(meta["slice_spacing"]),
            ct=data["ct"] if "ct" in data.files else None,
        )


def list_cases(cache_dir: Path) -> list[Path]:
    return sorted(Path(cache_dir).glob("*.npz"))
