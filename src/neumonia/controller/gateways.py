"""Pasarelas de la vista — Estrategia + DIP entre la UI y el backend.

- `LocalGateway`: la UI llama al controlador en el mismo proceso (modo escritorio / M1).
- `HttpGateway`: la UI llama a la API REST (modo cliente-servidor / M3-M4, Docker Compose).

La vista solo conoce `PredictionGateway` y elige la estrategia con NEUMONIA_API_URL.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import numpy as np
from PIL import Image

from neumonia.config import Settings, get_settings
from neumonia.controller.service import PneumoniaService
from neumonia.domain import Findings, Label, Prediction
from neumonia.model.readers import read_image


@dataclass(frozen=True)
class GatewayResult:
    prediction: Prediction
    original_rgb: np.ndarray


class PredictionGateway(Protocol):
    def predict(self, data: bytes, filename: str) -> GatewayResult: ...


def _original_rgb(data: bytes, filename: str) -> np.ndarray:
    return read_image(data, filename).pixels[:, :, ::-1].copy()


class LocalGateway:
    def __init__(self, service: PneumoniaService) -> None:
        self.service = service

    def predict(self, data: bytes, filename: str) -> GatewayResult:
        image = read_image(data, filename, self.service.readers)
        prediction = self.service.predict_image(image)
        return GatewayResult(prediction, image.pixels[:, :, ::-1].copy())


class GatewayError(RuntimeError):
    pass


class HttpGateway:
    def __init__(
        self, base_url: str, client: httpx.Client | None = None, timeout: float = 60.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=timeout)

    def predict(self, data: bytes, filename: str) -> GatewayResult:
        response = self.client.post(
            f"{self.base_url}/predict", files={"file": (filename, data, "application/octet-stream")}
        )
        if response.status_code != 200:
            raise GatewayError(f"La API respondió {response.status_code}: {response.text[:200]}")
        body: dict[str, Any] = response.json()
        heatmap = None
        if body.get("gradcam_url"):
            img = self.client.get(f"{self.base_url}{body['gradcam_url']}")
            if img.status_code == 200:
                heatmap = np.asarray(Image.open(io.BytesIO(img.content)).convert("RGB"))
        prediction = Prediction(
            label=Label(body["label"]),
            probability=float(body["probability"]),
            subtype=body.get("subtype", ""),
            class_probabilities=body.get("class_probabilities", {}),
            heatmap=heatmap,
            metadata=body.get("metadata", {}),
            findings=Findings.from_dict(body["findings"]) if body.get("findings") else None,
        )
        return GatewayResult(prediction, _original_rgb(data, filename))


def build_gateway(settings: Settings | None = None) -> PredictionGateway:
    settings = settings or get_settings()
    if settings.api_url:
        return HttpGateway(settings.api_url)
    from neumonia.controller.factory import get_service

    return LocalGateway(get_service())
