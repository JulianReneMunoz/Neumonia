"""Integración con el modelo real conv_MLP_84.h5 (se omite si no está descargado).

No se verifica exactitud (el curso no la evalúa): se verifica que el artefacto carga,
infiere sobre las muestras del aula y produce un Grad-CAM con el contrato correcto.
"""

from __future__ import annotations

import numpy as np
import pytest

from neumonia.config import Settings
from neumonia.controller.factory import build_service
from tests.conftest import MODEL_PATH, SAMPLE_FILES, requires_model

pytestmark = [requires_model, pytest.mark.model, pytest.mark.slow]


@pytest.fixture(scope="module")
def real_service():
    return build_service(Settings(model_path=MODEL_PATH))


def test_model_architecture(real_service):
    model = real_service.classifier.model
    assert tuple(model.inputs[0].shape[1:]) == (512, 512, 1)
    assert int(model.outputs[0].shape[-1]) == 3
    assert model.get_layer("conv10_thisone") is not None


@pytest.mark.parametrize("path", SAMPLE_FILES, ids=lambda p: p.name)
def test_real_inference_on_course_samples(real_service, path):
    prediction = real_service.predict_bytes(path.read_bytes(), path.name)
    assert prediction.label.value in {"NORMAL", "PNEUMONIA"}
    assert sum(prediction.class_probabilities.values()) == pytest.approx(1.0, abs=1e-4)
    assert prediction.heatmap.shape == (512, 512, 3)


def test_real_inference_is_deterministic(real_service):
    data = SAMPLE_FILES[0].read_bytes()
    a = real_service.predict_bytes(data, SAMPLE_FILES[0].name, explain=False)
    b = real_service.predict_bytes(data, SAMPLE_FILES[0].name, explain=False)
    assert a.class_probabilities == pytest.approx(b.class_probabilities)


def test_bacterial_sample_is_detected(real_service):
    path = next(p for p in SAMPLE_FILES if "bacteria" in p.name)
    assert real_service.predict_bytes(path.read_bytes(), path.name).label.value == "PNEUMONIA"


def test_gradcam_is_not_constant(real_service):
    path = SAMPLE_FILES[0]
    heatmap = real_service.predict_bytes(path.read_bytes(), path.name).heatmap
    assert np.std(heatmap) > 1.0
