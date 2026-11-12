"""Catálogo del dataset con metadatos (inspirado en *Datasheets for Datasets*, Gebru et al.).

Fuentes soportadas:
- `course`  : `data/JPG.zip` y `data/DICOM.zip` del aula (16 imágenes, smoke test).
- `rsna`    : RSNA Pneumonia Detection Challenge 2018 — 26 684 DICOM con edad, sexo y
              proyección en la cabecera + etiquetas y cajas de 6 radiólogos (dataset principal).
- `kermany` : Chest X-Ray Images (Kermany et al., 2018, CC BY 4.0) — 5 856 JPG con subtipo
              bacteriana/viral en el nombre (dataset con el que se entrenó conv_MLP_84).
"""

from __future__ import annotations

import csv
import random
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pydicom

from neumonia.model.metadata import age_group, extract_metadata

IMAGE_SUFFIXES = {".dcm", ".jpg", ".jpeg", ".png"}
METADATA_COLUMNS = (
    "image_path",
    "source",
    "target",
    "subtype",
    "rsna_class",
    "n_boxes",
    "age",
    "age_group",
    "sex",
    "view_position",
    "modality",
    "rows",
    "columns",
)


@dataclass
class Sample:
    image_path: str
    source: str
    target: int  # 1 = neumonía, 0 = normal
    subtype: str = ""
    rsna_class: str = ""
    n_boxes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        row = {k: v for k, v in asdict(self).items() if k != "metadata"}
        age = self.metadata.get("age")
        row.update(
            age=age if age is not None else "",
            age_group=age_group(age),
            sex=self.metadata.get("sex", ""),
            view_position=self.metadata.get("view_position", ""),
            modality=self.metadata.get("modality", ""),
            rows=self.metadata.get("rows", ""),
            columns=self.metadata.get("columns", ""),
        )
        return row


def subtype_from_name(name: str) -> str | None:
    """Deduce la clase desde el nombre o la carpeta (convención de Kermany y del aula)."""
    lowered = name.lower()
    if "bacteria" in lowered:
        return "bacteriana"
    if "virus" in lowered or "viral" in lowered:
        return "viral"
    if "normal" in lowered:
        return "normal"
    return None


def read_dicom_header(path: Path) -> dict[str, Any]:
    """Lee solo la cabecera (sin píxeles): rápido incluso con 26 000 archivos."""
    dataset = pydicom.dcmread(path, stop_before_pixels=True, force=True)
    return extract_metadata(dataset)


def scan_folder(root: Path, source: str = "course") -> list[Sample]:
    """Recorre una carpeta y etiqueta cada imagen por su nombre o el de su carpeta."""
    samples: list[Sample] = []
    for path in sorted(Path(root).rglob("*")):
        if path.suffix.lower() not in IMAGE_SUFFIXES or not path.is_file():
            continue
        subtype = subtype_from_name(path.name) or subtype_from_name(path.parent.name)
        if subtype is None:
            continue
        metadata = read_dicom_header(path) if path.suffix.lower() == ".dcm" else {}
        samples.append(
            Sample(
                image_path=str(path),
                source=source,
                target=int(subtype != "normal"),
                subtype=subtype,
                metadata=metadata,
            )
        )
    return samples


def load_rsna(root: Path, read_headers: bool = True, limit: int | None = None) -> list[Sample]:
    """Carga el RSNA Pneumonia Detection Challenge (estructura de Kaggle, stage 2)."""
    root = Path(root)
    labels_csv = root / "stage_2_train_labels.csv"
    classes_csv = root / "stage_2_detailed_class_info.csv"
    images_dir = root / "stage_2_train_images"
    if not labels_csv.is_file():
        raise FileNotFoundError(f"No se encontró {labels_csv}. Ejecute `make dataset-rsna`.")

    targets: dict[str, int] = {}
    boxes: dict[str, int] = defaultdict(int)
    with labels_csv.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pid = row["patientId"]
            target = int(row["Target"])
            targets[pid] = max(targets.get(pid, 0), target)
            boxes[pid] += target
    classes: dict[str, str] = {}
    if classes_csv.is_file():
        with classes_csv.open(encoding="utf-8") as handle:
            classes = {row["patientId"]: row["class"] for row in csv.DictReader(handle)}

    samples: list[Sample] = []
    for pid, target in targets.items():
        if limit is not None and len(samples) >= limit:
            break
        path = images_dir / f"{pid}.dcm"
        metadata = read_dicom_header(path) if read_headers and path.is_file() else {}
        samples.append(
            Sample(
                image_path=str(path),
                source="rsna",
                target=target,
                subtype="neumonia" if target else "normal",
                rsna_class=classes.get(pid, ""),
                n_boxes=boxes[pid],
                metadata=metadata,
            )
        )
    return samples


def stratified_subset(samples: list[Sample], n: int, seed: int = 42) -> list[Sample]:
    """Submuestra de tamaño n que conserva la proporción de clases (reproducible por semilla)."""
    if n >= len(samples):
        return list(samples)
    rng = random.Random(seed)  # noqa: S311 - muestreo reproducible, no criptografía
    by_target: dict[int, list[Sample]] = defaultdict(list)
    for sample in samples:
        by_target[sample.target].append(sample)
    chosen: list[Sample] = []
    for target, group in sorted(by_target.items()):
        quota = round(n * len(group) / len(samples))
        chosen.extend(rng.sample(group, min(quota, len(group))))
        del target
    rng.shuffle(chosen)
    return chosen[:n]


def write_metadata_csv(samples: list[Sample], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        for sample in samples:
            writer.writerow(sample.to_row())
    return path


def read_metadata_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def extract_course_zips(data_dir: Path, dest: Path) -> Path:
    """Descomprime JPG.zip y DICOM.zip del aula en `dest` (idempotente)."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("JPG.zip", "DICOM.zip"):
        archive = Path(data_dir) / name
        if not archive.is_file():
            continue
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                target = (dest / member).resolve()
                if not target.is_relative_to(dest.resolve()):
                    raise ValueError(f"Ruta insegura en el ZIP: {member}")  # zip-slip
            zf.extractall(dest)
    return dest


def summarize(samples: list[Sample]) -> dict[str, Any]:
    """Resumen para la datasheet: tamaño, balance de clases y cobertura de metadatos."""
    total = len(samples)
    positives = sum(s.target for s in samples)
    by_sex: dict[str, int] = defaultdict(int)
    by_view: dict[str, int] = defaultdict(int)
    by_age: dict[str, int] = defaultdict(int)
    for s in samples:
        by_sex[s.metadata.get("sex", "desconocido")] += 1
        by_view[s.metadata.get("view_position", "desconocido")] += 1
        by_age[age_group(s.metadata.get("age"))] += 1
    return {
        "total": total,
        "neumonia": positives,
        "normal": total - positives,
        "prevalencia": round(positives / total, 4) if total else 0.0,
        "por_sexo": dict(by_sex),
        "por_proyeccion": dict(by_view),
        "por_edad": dict(by_age),
    }
