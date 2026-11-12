"""Controlador con dobles de prueba (sin TensorFlow)."""

from __future__ import annotations

import pytest

from neumonia.controller.service import PneumoniaService
from neumonia.domain import Label, Prediction
from neumonia.model.readers import InvalidImageError
from tests.conftest import FakeClassifier, FakeExplainer


def test_predict_bytes_happy_path(fake_service, png_bytes_sample, fake_classifier):
    # Act
    prediction = fake_service.predict_bytes(png_bytes_sample, "rx.png")
    # Assert
    assert prediction.label is Label.PNEUMONIA
    assert prediction.probability == pytest.approx(0.8)
    assert prediction.subtype == "bacteriana"
    assert fake_classifier.calls == [(1, 512, 512, 1)]


def test_heatmap_is_rgb_512(fake_service, png_bytes_sample):
    prediction = fake_service.predict_bytes(png_bytes_sample, "rx.png")
    assert prediction.heatmap.shape == (512, 512, 3)


def test_gradcam_targets_decided_subtype(png_bytes_sample):
    explainer = FakeExplainer()
    service = PneumoniaService(FakeClassifier((0.1, 0.2, 0.7)), explainer)
    service.predict_bytes(png_bytes_sample, "rx.png")
    assert explainer.class_indices == [2]


def test_explain_false_skips_gradcam(fake_service, png_bytes_sample, fake_explainer):
    prediction = fake_service.predict_bytes(png_bytes_sample, "rx.png", explain=False)
    assert prediction.heatmap is None
    assert fake_explainer.class_indices == []


def test_without_explainer_heatmap_is_none(png_bytes_sample):
    prediction = PneumoniaService(FakeClassifier()).predict_bytes(png_bytes_sample, "rx.png")
    assert prediction.heatmap is None


def test_explainer_factory_is_lazy(png_bytes_sample):
    # Arrange
    built = []

    def factory():
        built.append(1)
        return FakeExplainer()

    service = PneumoniaService(FakeClassifier(), factory)
    # Assert: no se construye hasta la primera predicción, y solo una vez
    assert built == []
    service.predict_bytes(png_bytes_sample, "rx.png")
    service.predict_bytes(png_bytes_sample, "rx.png")
    assert built == [1]


def test_dicom_metadata_flows_to_prediction(fake_service, dicom_bytes_sample):
    prediction = fake_service.predict_bytes(dicom_bytes_sample, "rx.dcm")
    assert prediction.metadata["sex"] == "M"


def test_class_probabilities_are_named(fake_service, jpg_bytes_sample):
    prediction = fake_service.predict_bytes(jpg_bytes_sample, "rx.jpg")
    assert prediction.class_probabilities == pytest.approx(
        {"bacteriana": 0.7, "normal": 0.2, "viral": 0.1}
    )


def test_invalid_bytes_raise(fake_service):
    with pytest.raises(InvalidImageError):
        fake_service.predict_bytes(b"no soy una imagen", "rx.txt")


def test_to_contract_has_required_keys(fake_service, png_bytes_sample):
    payload = fake_service.predict_bytes(png_bytes_sample, "rx.png").to_contract(
        "/static/x.png", "v1"
    )
    assert {"label", "probability", "gradcam_url"} <= set(payload)
    assert payload["label"] in {"NORMAL", "PNEUMONIA"}
    assert payload["model_version"] == "v1"


def test_to_contract_rounds_probability():
    prediction = Prediction(Label.NORMAL, 0.123456789, "normal", {"normal": 0.123456789})
    assert prediction.to_contract(None, "v")["probability"] == 0.1235
