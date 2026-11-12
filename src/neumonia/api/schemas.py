"""Esquemas Pydantic del contrato REST. Fuente de verdad: `api/openapi.yaml`."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    label: Literal["NORMAL", "PNEUMONIA"] = Field(description="Decisión binaria del contrato.")
    probability: float = Field(ge=0.0, le=1.0, description="Probabilidad de la etiqueta devuelta.")
    gradcam_url: str | None = Field(description="Ruta relativa del PNG con Grad-CAM.")
    subtype: str = Field(description="Clase original del modelo: bacteriana | normal | viral.")
    class_probabilities: dict[str, float]
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadatos DICOM no sensibles."
    )
    model_version: str
    request_id: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    model_version: str


class ErrorResponse(BaseModel):
    error: str
