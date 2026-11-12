"""Configuración central del proyecto (12-factor: todo se puede sobreescribir por entorno).

Ningún otro módulo lee variables de entorno directamente: piden `get_settings()`.
Así las pruebas pueden inyectar una configuración distinta sin tocar el sistema.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_URL = (
    "https://github.com/jorgeenrgutierrez-gif/uao-neumonia/releases/download/"
    "modelo-v1/conv_MLP_84.h5"
)
MODEL_SHA256 = "d9548ff6fd2c29cdd15328ff95e1ad1fc8c7226e04e86c5890526bea2215e18e"
MODEL_VERSION = "conv_MLP_84@modelo-v1"

IMG_SIZE = 512
GRADCAM_LAYER = "conv10_thisone"
CLASS_NAMES: tuple[str, ...] = ("bacteriana", "normal", "viral")
NORMAL_INDEX = 1


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else default


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución. Inmutable para que nadie la modifique en caliente."""

    model_path: Path = field(
        default_factory=lambda: PROJECT_ROOT / "artifacts" / "model" / "conv_MLP_84.h5"
    )
    model_url: str = MODEL_URL
    model_sha256: str = MODEL_SHA256
    model_version: str = MODEL_VERSION
    threshold: float = 0.5
    static_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "runtime" / "static")
    history_path: Path = field(default_factory=lambda: PROJECT_ROOT / "runtime" / "historial.csv")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "runtime" / "reports")
    max_upload_mb: float = 20.0
    max_gradcam_files: int = 200
    api_url: str | None = None
    mlflow_tracking_uri: str = (
        "sqlite:///mlflow.db"  # MLflow 3: el file store está en mantenimiento
    )

    @classmethod
    def from_env(cls) -> Settings:
        base = cls()
        return cls(
            model_path=_env_path("NEUMONIA_MODEL_PATH", base.model_path),
            threshold=_env_float("NEUMONIA_THRESHOLD", base.threshold),
            static_dir=_env_path("NEUMONIA_STATIC_DIR", base.static_dir),
            history_path=_env_path("NEUMONIA_HISTORY_PATH", base.history_path),
            reports_dir=_env_path("NEUMONIA_REPORTS_DIR", base.reports_dir),
            max_upload_mb=_env_float("NEUMONIA_MAX_UPLOAD_MB", base.max_upload_mb),
            api_url=os.environ.get("NEUMONIA_API_URL") or None,
            mlflow_tracking_uri=os.environ.get("MLFLOW_TRACKING_URI", base.mlflow_tracking_uri),
        )

    def __post_init__(self) -> None:
        if not 0.0 < self.threshold < 1.0:
            raise ValueError("El umbral debe estar en el intervalo abierto (0, 1).")
        if self.max_upload_mb <= 0:
            raise ValueError("max_upload_mb debe ser positivo.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
