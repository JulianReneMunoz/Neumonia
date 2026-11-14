"""Raíz de composición: el ÚNICO lugar que conoce las clases concretas (Keras, Grad-CAM).

Vista, API y gRPC piden `build_service()`; las pruebas construyen el servicio con dobles.
"""

from __future__ import annotations

from functools import lru_cache

from neumonia.config import Settings, get_settings
from neumonia.controller.decision import ThresholdPolicy
from neumonia.controller.service import PneumoniaService
from neumonia.model.classifier import KerasClassifier
from neumonia.model.lung_segmentation import (
    GeometricLungSegmenter,
    IsolatedLungSegmenter,
    LungSegmenter,
    QualityCheckedSegmenter,
)


def build_segmenter(settings: Settings) -> LungSegmenter:
    """`pspnet` corre en un proceso aparte (PyTorch y TensorFlow no conviven) y siempre va
    envuelto en el control de calidad con respaldo geométrico."""
    if settings.lung_segmenter == "pspnet":
        return QualityCheckedSegmenter(IsolatedLungSegmenter(), GeometricLungSegmenter())
    return GeometricLungSegmenter()


def build_service(settings: Settings | None = None) -> PneumoniaService:
    settings = settings or get_settings()
    classifier = KerasClassifier(settings.model_path)

    def explainer_factory():
        from neumonia.model.gradcam import GradCamExplainer

        return GradCamExplainer(classifier.model)

    return PneumoniaService(
        classifier=classifier,
        explainer=explainer_factory,
        policy=ThresholdPolicy(settings.threshold),
        segmenter=build_segmenter(settings),
    )


@lru_cache(maxsize=1)
def get_service() -> PneumoniaService:
    return build_service()
