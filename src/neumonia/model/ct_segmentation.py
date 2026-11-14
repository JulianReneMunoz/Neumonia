"""Prototipo de tomografía: segmentación volumétrica con MEDPSeg (ADR-0010).

MEDPSeg (Carmo et al., SPIE Medical Imaging 2026; licencia MIT) segmenta en una tomografía de tórax:
pulmón izquierdo/derecho, lesión (vidrio esmerilado + consolidación), vía aérea, vasos y lóbulos.
Corre en **su propio entorno** (PyTorch 2.8) y se invoca como proceso externo con
`medpseg_runner.py`; la app solo lee sus NIfTI. Así no choca con TensorFlow ni con PSPNet.

Las máscaras se reorientan a RAS+ (x hacia la derecha del paciente, y anterior, z superior).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

STRUCTURES = (
    "pulmon_derecho",
    "pulmon_izquierdo",
    "vidrio_esmerilado",
    "consolidacion",
    "via_aerea",
    "vasos",
)
RUNNER = Path(__file__).with_name("medpseg_runner.py")
# Sufijos de los archivos que escribe MEDPSeg: <caso><sufijo>.nii.gz
MEDPSEG_SUFFIXES = {
    "lr_lung": "_lr_lung",  # 1 = pulmón izquierdo, 2 = pulmón derecho
    "ggo": "_ggo",
    "consolidation": "_consolidation",
    "airway": "_airway",
    "vessel": "_vessel",
    "lobes": "_lobes",
}


@dataclass(frozen=True)
class CtSegmentation:
    """Máscaras booleanas (x, y, z) en RAS+ y el espaciado de vóxel en mm."""

    case_id: str
    spacing: tuple[float, float, float]
    masks: dict[str, np.ndarray]
    lobes: np.ndarray | None = None  # etiquetas enteras de lóbulo (0 = fondo)
    ct: np.ndarray | None = None  # unidades Hounsfield, para los cortes

    def __post_init__(self) -> None:
        missing = set(STRUCTURES) - set(self.masks)
        if missing:
            raise ValueError(f"Faltan máscaras: {sorted(missing)}")
        shapes = {mask.shape for mask in self.masks.values()}
        if len(shapes) != 1 or len(next(iter(shapes))) != 3:
            raise ValueError("Todas las máscaras deben ser 3D y de la misma forma.")

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.masks["pulmon_derecho"].shape

    @property
    def voxel_ml(self) -> float:
        return float(np.prod(self.spacing)) / 1000.0

    @property
    def lesion(self) -> np.ndarray:
        return self.masks["vidrio_esmerilado"] | self.masks["consolidacion"]


def _load_canonical(path: Path, reference=None):
    """Lee un NIfTI en RAS+. Con `reference`, usa la geometría de esa imagen: MEDPSeg guarda los
    lóbulos (vía MONAI) con metadatos inconsistentes pero sobre la misma rejilla de vóxeles."""
    import nibabel as nib

    image = nib.load(str(path))
    if reference is not None and image.shape[:3] == reference.shape[:3]:
        image = nib.Nifti1Image(np.asarray(image.dataobj), reference.affine)
    image = nib.as_closest_canonical(image)
    return np.asarray(image.dataobj), tuple(float(z) for z in image.header.get_zooms()[:3])


def find_output(out_dir: Path, case_id: str, key: str) -> Path | None:
    candidates = sorted(Path(out_dir).glob(f"{case_id}*{MEDPSEG_SUFFIXES[key]}.nii.gz"))
    return candidates[0] if candidates else None


def load_medpseg_output(out_dir: Path, case_id: str, ct_path: Path | None = None) -> CtSegmentation:
    """Lee los NIfTI de MEDPSeg (y opcionalmente la tomografía) en un `CtSegmentation`."""
    out_dir = Path(out_dir)
    lr_path = find_output(out_dir, case_id, "lr_lung")
    if lr_path is None:
        raise FileNotFoundError(f"No hay salida de MEDPSeg para {case_id} en {out_dir}")
    import nibabel as nib

    reference = nib.load(str(lr_path))
    lr, spacing = _load_canonical(lr_path)
    masks = {"pulmon_izquierdo": lr == 1, "pulmon_derecho": lr == 2}
    for key, name in (
        ("ggo", "vidrio_esmerilado"),
        ("consolidation", "consolidacion"),
        ("airway", "via_aerea"),
        ("vessel", "vasos"),
    ):
        path = find_output(out_dir, case_id, key)
        masks[name] = (
            (_load_canonical(path, reference)[0] > 0) if path else np.zeros(lr.shape, bool)
        )
    lobes_path = find_output(out_dir, case_id, "lobes")
    lobes = _load_canonical(lobes_path, reference)[0].astype(np.uint8) if lobes_path else None
    if lobes is not None and lobes.shape != lr.shape:
        lobes = None
    ct = None
    if ct_path is not None and Path(ct_path).is_file():
        volume, _ = _load_canonical(Path(ct_path))
        ct = volume.astype(np.int16) if volume.shape == lr.shape else None
    return CtSegmentation(case_id, spacing, masks, lobes, ct)


class MedpsegSegmenter:
    """Llama a MEDPSeg en su entorno (`NEUMONIA_MEDPSEG_PYTHON`) y lee el resultado."""

    def __init__(self, python: Path, spacing: float = 1.5, timeout: float = 4 * 3600) -> None:
        self.python = Path(python)
        self.spacing = spacing
        self.timeout = timeout

    def command(self, ct_path: Path, out_dir: Path) -> list[str]:
        return [
            str(self.python),
            str(RUNNER),
            str(ct_path),
            str(out_dir),
            "--spacing",
            str(self.spacing),
        ]

    def segment(self, ct_path: Path, out_dir: Path) -> CtSegmentation:
        if not self.python.is_file():
            raise FileNotFoundError(
                f"No existe {self.python}. Ejecute `make ct-setup` y configure "
                "NEUMONIA_MEDPSEG_PYTHON."
            )
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(  # noqa: S603 - ejecutable configurado por el operador
            self.command(Path(ct_path), out_dir),
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        if result.returncode != 0 or "MEDPSEG_OK" not in result.stdout:
            tail = (result.stderr or result.stdout).strip().splitlines()[-5:]
            raise RuntimeError("MEDPSeg falló:\n" + "\n".join(tail))
        case_id = Path(ct_path).name.replace(".nii.gz", "").replace(".nii", "")
        resampled = out_dir / f"{case_id}.nii.gz"
        return load_medpseg_output(
            out_dir, case_id, resampled if resampled.is_file() else Path(ct_path)
        )


def python_in_env(env_dir: Path) -> Path:
    """Ruta del intérprete dentro de un entorno virtual (Windows o Unix)."""
    sub = ("Scripts", "python.exe") if sys.platform == "win32" else ("bin", "python")
    return Path(env_dir).joinpath(*sub)
