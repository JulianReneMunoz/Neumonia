"""Fixtures compartidas. Los dobles de prueba permiten probar el controlador sin TensorFlow."""

from __future__ import annotations

import io
import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from neumonia.config import CLASS_NAMES, Settings
from neumonia.controller.service import PneumoniaService

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "artifacts" / "samples"
EXPECTED = ROOT / "artifacts" / "expected" / "response_example.json"
MODEL_PATH = ROOT / "artifacts" / "model" / "conv_MLP_84.h5"
SAMPLE_FILES = sorted(
    p for p in SAMPLES.iterdir() if p.suffix.lower() in {".dcm", ".jpeg", ".jpg", ".png"}
)


class FakeClassifier:
    """Devuelve siempre las mismas probabilidades y registra lo que recibe."""

    class_names = CLASS_NAMES
    is_loaded = True

    def __init__(self, probs=(0.7, 0.2, 0.1)) -> None:
        self.probs = np.asarray(probs, dtype=float)
        self.calls: list[tuple[int, ...]] = []

    def predict_proba(self, batch: np.ndarray) -> np.ndarray:
        self.calls.append(batch.shape)
        return self.probs


class FakeExplainer:
    def __init__(self) -> None:
        self.class_indices: list[int] = []

    def explain(self, batch: np.ndarray, class_index: int) -> np.ndarray:
        self.class_indices.append(class_index)
        heat = np.zeros((31, 31))
        heat[10:20, 10:20] = 1.0
        return heat


class ExplodingClassifier:
    class_names = CLASS_NAMES

    def predict_proba(self, batch):
        raise RuntimeError("fallo interno simulado")


def make_dicom_bytes(
    pixels: np.ndarray,
    photometric: str = "MONOCHROME2",
    age: str = "045Y",
    sex: str = "M",
    view: str = "PA",
    patient_id: str = "SECRETO-123",
) -> bytes:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    ds.PatientID = patient_id
    ds.PatientName = "Paciente^Prueba"
    ds.PatientAge = age
    ds.PatientSex = sex
    ds.ViewPosition = view
    ds.Modality = "CR"
    ds.BodyPartExamined = "CHEST"
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = photometric
    bits = 16 if pixels.dtype == np.uint16 else 8
    ds.BitsAllocated = bits
    ds.BitsStored = bits
    ds.HighBit = bits - 1
    ds.PixelRepresentation = 0
    ds.PixelData = pixels.tobytes()
    buffer = io.BytesIO()
    ds.save_as(buffer, enforce_file_format=True)
    return buffer.getvalue()


def encode(array: np.ndarray, ext: str = ".png") -> bytes:
    ok, buf = cv2.imencode(ext, array)
    assert ok
    return buf.tobytes()


@pytest.fixture
def gradient_image() -> np.ndarray:
    row = np.linspace(0, 255, 256, dtype=np.uint8)
    return np.tile(row, (256, 1))


@pytest.fixture
def png_bytes_sample(gradient_image) -> bytes:
    return encode(gradient_image, ".png")


@pytest.fixture
def jpg_bytes_sample(gradient_image) -> bytes:
    return encode(gradient_image, ".jpg")


@pytest.fixture
def dicom_bytes_sample(gradient_image) -> bytes:
    return make_dicom_bytes(gradient_image)


@pytest.fixture
def fake_classifier() -> FakeClassifier:
    return FakeClassifier()


@pytest.fixture
def fake_explainer() -> FakeExplainer:
    return FakeExplainer()


@pytest.fixture
def fake_service(fake_classifier, fake_explainer) -> PneumoniaService:
    return PneumoniaService(classifier=fake_classifier, explainer=fake_explainer)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        static_dir=tmp_path / "static",
        history_path=tmp_path / "historial.csv",
        reports_dir=tmp_path / "reports",
        max_upload_mb=1.0,
    )


@pytest.fixture(scope="session")
def tiny_keras_model(tmp_path_factory):
    """Red mínima con la misma interfaz que conv_MLP_84 (512×512×1 → 3, capa conv10_thisone)."""
    import tensorflow as tf

    inputs = tf.keras.Input(shape=(512, 512, 1))
    x = tf.keras.layers.Conv2D(4, 3, strides=8, activation="relu")(inputs)
    x = tf.keras.layers.Conv2D(8, 3, strides=2, activation="relu", name="conv10_thisone")(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    outputs = tf.keras.layers.Dense(3, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    path = tmp_path_factory.mktemp("model") / "tiny.h5"
    model.save(path)
    return path


requires_model = pytest.mark.skipif(
    not MODEL_PATH.is_file(), reason="Modelo real no descargado (make model)"
)
