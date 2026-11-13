"""Segmentación de los campos pulmonares (Estrategia `LungSegmenter`, ADR-0008).

Implementaciones intercambiables:
- `GeometricLungSegmenter` (por defecto): rectángulos aproximados, sin dependencias.
- `XrvLungSegmenter`: PSPNet preentrenada de TorchXRayVision (14 estructuras anatómicas, 512×512).
  PyTorch se importa de forma perezosa y solo si se instaló el extra `seg`.
- `IsolatedLungSegmenter`: ejecuta otro segmentador en un **proceso hijo persistente**.
  Es necesario porque TensorFlow y `torchvision` registran las mismas opciones de LLVM y
  abortan si conviven en el mismo proceso
  ("LLVM ERROR: inconsistency in registered CommandLine options").
- `QualityCheckedSegmenter` (decorador): usa el segmentador principal y, si falla o la máscara no
  supera el control de calidad, vuelve al geométrico y deja la razón en `LungMasks.note`.

Limitación conocida: la consolidación densa (justo la neumonía) se parece a tejido blando y los
segmentadores tienden a recortar esa parte del pulmón; por eso existe el control de calidad.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

import cv2
import numpy as np

from neumonia.config import IMG_SIZE
from neumonia.domain import LungMasks
from neumonia.model.lung_worker import read_frame, write_frame

# Fracción de la imagen ocupada por los campos pulmonares (rectángulos de referencia).
TOP, BOTTOM = 0.12, 0.88
RIGHT_LUNG_X = (0.08, 0.47)  # mitad izquierda de la imagen = pulmón derecho del paciente
LEFT_LUNG_X = (0.53, 0.92)

PSPNET_INPUT = 512
PSPNET_THRESHOLD = 0.5
PSPNET_WEIGHTS = "pspnet_chestxray_best_model_4.pth"
PSPNET_SHA256 = "019b167eac6b729fc1bb92bbbc185fc1730aaa65819f4e3fe718186cadc044fc"
PSPNET_TARGETS: tuple[str, ...] = (
    "Left Clavicle", "Right Clavicle", "Left Scapula", "Right Scapula", "Left Lung", "Right Lung",
    "Left Hilus Pulmonis", "Right Hilus Pulmonis", "Heart", "Aorta", "Facies Diaphragmatica",
    "Mediastinum", "Weasand", "Spine",
)  # fmt: skip
MIN_LUNG_AREA = 0.04  # cada pulmón debe ocupar al menos el 4 % de la imagen
MIN_FIELD_AREA = 0.12  # y ambos juntos al menos el 12 %


@runtime_checkable
class LungSegmenter(Protocol):
    name: str

    def segment(self, pixels: np.ndarray, size: int = IMG_SIZE) -> LungMasks: ...


def geometric_masks(size: int = IMG_SIZE, note: str = "") -> LungMasks:
    r0, r1 = int(TOP * size), int(BOTTOM * size)
    right = np.zeros((size, size), dtype=bool)
    left = np.zeros((size, size), dtype=bool)
    right[r0:r1, int(RIGHT_LUNG_X[0] * size) : int(RIGHT_LUNG_X[1] * size)] = True
    left[r0:r1, int(LEFT_LUNG_X[0] * size) : int(LEFT_LUNG_X[1] * size)] = True
    return LungMasks(right=right, left=left, source="geometrica", note=note)


class GeometricLungSegmenter:
    """Campos pulmonares rectangulares aproximados (no mira la imagen)."""

    name = "geometrica"

    def segment(self, pixels: np.ndarray, size: int = IMG_SIZE) -> LungMasks:
        return geometric_masks(size)


def to_gray(pixels: np.ndarray, size: int = PSPNET_INPUT) -> np.ndarray:
    gray = pixels if pixels.ndim == 2 else cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
    return cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)


def clean_mask(mask: np.ndarray) -> np.ndarray:
    """Conserva el componente conexo más grande y rellena sus huecos."""
    binary = np.asarray(mask, dtype=np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 1:
        return np.zeros(binary.shape, dtype=bool)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    component = (labels == largest).astype(np.uint8)
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(component)
    cv2.drawContours(filled, contours, -1, 1, thickness=cv2.FILLED)
    return filled.astype(bool)


def resize_mask(mask: np.ndarray, size: int) -> np.ndarray:
    if mask.shape == (size, size):
        return mask.astype(bool)
    resized = cv2.resize(mask.astype(np.uint8), (size, size), interpolation=cv2.INTER_NEAREST)
    return resized.astype(bool)


def quality_problem(masks: LungMasks) -> str | None:
    """Devuelve la razón por la que la segmentación no es confiable, o None si es aceptable."""
    right_area = float(masks.right.mean())
    left_area = float(masks.left.mean())
    if min(right_area, left_area) < MIN_LUNG_AREA:
        return (
            f"un pulmón ocupa solo el {100 * min(right_area, left_area):.0f} % de la imagen "
            "(posible consolidación densa, placa pediátrica, rotada o recortada)"
        )
    if right_area + left_area < MIN_FIELD_AREA:
        return f"los pulmones ocupan solo el {100 * (right_area + left_area):.0f} % de la imagen"
    right_x = float(np.nonzero(masks.right)[1].mean())
    left_x = float(np.nonzero(masks.left)[1].mean())
    if right_x >= left_x:
        return "los pulmones aparecen invertidos (¿imagen volteada o proyección lateral?)"
    if (masks.right & masks.left).any():
        return "las máscaras de ambos pulmones se superponen"
    return None


class XrvLungSegmenter:
    """PSPNet de TorchXRayVision (Lingling et al., ChestX-Det). Requiere `uv sync --extra seg`.

    `predict_fn` recibe la imagen en gris 512×512 normalizada como espera TorchXRayVision
    ([-1024, 1024]) y devuelve probabilidades (14, 512, 512). Se inyecta en las pruebas.
    """

    name = "pspnet"

    def __init__(
        self,
        predict_fn: Callable[[np.ndarray], np.ndarray] | None = None,
        targets: tuple[str, ...] | None = None,
        threshold: float = PSPNET_THRESHOLD,
    ) -> None:
        self._predict_fn = predict_fn
        self._targets = targets or PSPNET_TARGETS
        self.threshold = threshold

    def _load(self) -> None:  # pragma: no cover - requiere torch + pesos (prueba con marca model)
        try:
            import torch
            import torchxrayvision as xrv
        except ImportError as exc:
            raise RuntimeError("falta el extra de segmentación; ejecute `make seg`") from exc

        model = xrv.baseline_models.chestx_det.PSPNet()
        model.eval()
        verify_weights()

        def predict(image: np.ndarray) -> np.ndarray:
            with torch.no_grad():
                logits = model(torch.from_numpy(image[None, None].astype(np.float32)))
            return torch.sigmoid(logits)[0].numpy()

        self._predict_fn = predict
        self._targets = tuple(model.targets)

    def segment(self, pixels: np.ndarray, size: int = IMG_SIZE) -> LungMasks:
        if self._predict_fn is None:
            self._load()
        if self._predict_fn is None:
            raise RuntimeError("PSPNet no está disponible.")
        gray = to_gray(pixels).astype(np.float32)
        normalized = (2.0 * (gray / 255.0) - 1.0) * 1024.0  # = xrv.datasets.normalize(x, 255)
        probs = np.asarray(self._predict_fn(normalized))
        # TorchXRayVision usa nombres anatómicos: "Right Lung" = pulmón derecho del paciente.
        right = clean_mask(probs[self._targets.index("Right Lung")] > self.threshold)
        left = clean_mask(probs[self._targets.index("Left Lung")] > self.threshold)
        return LungMasks(
            right=resize_mask(right, size), left=resize_mask(left, size), source="pspnet"
        )


class IsolatedLungSegmenter:
    """Corre el segmentador en un proceso hijo persistente (`python -m neumonia.model.lung_worker`).

    El hijo se crea en la primera llamada y se reutiliza; si muere, la siguiente llamada lo
    vuelve a crear. `factory` es "módulo:atributo" de una clase o función sin argumentos.
    """

    def __init__(
        self,
        factory: str = "neumonia.model.lung_segmentation:XrvLungSegmenter",
        name: str = "pspnet",
    ) -> None:
        self.factory = factory
        self.name = name
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    def _start(self) -> subprocess.Popen[bytes]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(path for path in sys.path if path)
        return subprocess.Popen(  # noqa: S603 - ejecutable y módulo propios, sin entrada externa
            [sys.executable, "-m", "neumonia.model.lung_worker", self.factory],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env,
        )

    def segment(self, pixels: np.ndarray, size: int = IMG_SIZE) -> LungMasks:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                self._process = self._start()
            stdin, stdout = self._process.stdin, self._process.stdout
            if stdin is None or stdout is None:  # pragma: no cover - PIPE garantizado
                raise RuntimeError("Canal del proceso de segmentación no disponible.")
            try:
                write_frame(stdin, (np.ascontiguousarray(pixels), size))
                status, payload = read_frame(stdout)
            except (EOFError, BrokenPipeError, OSError) as exc:
                self.close()
                raise RuntimeError(f"el proceso de segmentación terminó ({exc})") from exc
        if status != "ok":
            raise RuntimeError(payload)
        return payload

    def close(self) -> None:
        if self._process is not None:
            if self._process.poll() is None:
                self._process.kill()
            self._process.wait(timeout=10)
            self._process = None


class QualityCheckedSegmenter:
    """Decorador: segmentador principal con control de calidad y respaldo geométrico."""

    def __init__(self, primary: LungSegmenter, fallback: LungSegmenter | None = None) -> None:
        self.primary = primary
        self.fallback = fallback or GeometricLungSegmenter()
        self.name = primary.name

    def segment(self, pixels: np.ndarray, size: int = IMG_SIZE) -> LungMasks:
        try:
            masks = self.primary.segment(pixels, size)
        except Exception as exc:  # dependencia ausente, pesos corruptos, imagen rara...
            reason = f"no se pudo segmentar ({exc or type(exc).__name__})"
        else:
            reason = quality_problem(masks)
            if reason is None:
                return masks
        fallback = self.fallback.segment(pixels, size)
        note = f"Segmentación {self.primary.name} descartada: {reason}. Se usan zonas geométricas."
        return LungMasks(fallback.right, fallback.left, fallback.source, note)


def weights_path() -> Path:
    return Path.home() / ".torchxrayvision" / "models_data" / PSPNET_WEIGHTS


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_weights(path: Path | None = None) -> None:
    """Integridad de los pesos descargados por TorchXRayVision (igual que con conv_MLP_84)."""
    path = path or weights_path()
    if path.exists() and sha256_of(path) != PSPNET_SHA256:
        raise RuntimeError(f"SHA-256 inesperado en {path}; bórrelo para descargarlo de nuevo.")
