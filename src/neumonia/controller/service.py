"""Controlador principal (antes `integrator.py`): leer → preprocesar → predecir → explicar.

Solo depende de abstracciones (`Classifier`, `Explainer`, `DecisionPolicy`, lectores),
que recibe por el constructor (inyección de dependencias). Por eso se prueba sin TensorFlow.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from neumonia.config import CLASS_NAMES
from neumonia.controller.decision import DecisionPolicy, ThresholdPolicy
from neumonia.controller.findings import with_summary
from neumonia.domain import Prediction, RadiographImage
from neumonia.model.classifier import Classifier
from neumonia.model.gradcam import Explainer, overlay_heatmap
from neumonia.model.localization import analyze_attention
from neumonia.model.preprocessing import preprocess
from neumonia.model.readers import DEFAULT_READERS, ImageReader, read_image


class PneumoniaService:
    def __init__(
        self,
        classifier: Classifier,
        explainer: Explainer | Callable[[], Explainer] | None = None,
        policy: DecisionPolicy | None = None,
        readers: tuple[ImageReader, ...] = DEFAULT_READERS,
    ) -> None:
        self.classifier = classifier
        self._explainer = explainer
        self.policy = policy or ThresholdPolicy()
        self.readers = readers

    @property
    def explainer(self) -> Explainer | None:
        """Admite una fábrica perezosa: el Grad-CAM se construye la primera vez que se usa."""
        if self._explainer is not None and not isinstance(self._explainer, Explainer):
            self._explainer = self._explainer()
        return self._explainer

    def predict_image(self, image: RadiographImage, explain: bool = True) -> Prediction:
        batch = preprocess(image.pixels)
        probs = np.asarray(self.classifier.predict_proba(batch), dtype=np.float64)
        decision = self.policy.decide(probs)
        names = getattr(self.classifier, "class_names", CLASS_NAMES)
        heatmap = None
        findings = None
        explainer = self.explainer if explain else None
        if explainer is not None:
            cam = explainer.explain(batch, decision.target_index)
            heatmap = overlay_heatmap(cam, image.pixels)
            findings = with_summary(
                analyze_attention(cam), decision.label, decision.probability, decision.subtype
            )
        return Prediction(
            label=decision.label,
            probability=decision.probability,
            subtype=decision.subtype,
            class_probabilities={name: float(p) for name, p in zip(names, probs, strict=True)},
            heatmap=heatmap,
            metadata=dict(image.metadata),
            findings=findings,
        )

    def predict_bytes(
        self, data: bytes, filename: str | None = None, explain: bool = True
    ) -> Prediction:
        return self.predict_image(read_image(data, filename, self.readers), explain=explain)
