"""Lectura de imágenes (Estrategia): DICOM, JPG/PNG y entradas inválidas."""

from __future__ import annotations

import numpy as np
import pytest

from neumonia.model.readers import (
    DicomReader,
    InvalidImageError,
    RasterReader,
    read_image,
    read_path,
    select_reader,
    to_three_channels,
    to_uint8,
)
from tests.conftest import SAMPLE_FILES, encode, make_dicom_bytes


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("x.dcm", DicomReader),
        ("x.DICOM", DicomReader),
        ("x.jpg", RasterReader),
        ("x.jpeg", RasterReader),
        ("x.png", RasterReader),
        ("x.bmp", RasterReader),
    ],
)
def test_select_reader_by_extension(filename, expected):
    # Arrange: bytes sin firma reconocible, solo decide la extensión
    data = b"sin-firma-conocida"
    # Act
    reader = select_reader(filename, data)
    # Assert
    assert isinstance(reader, expected)


def test_select_reader_prefers_signature_over_extension(png_bytes_sample):
    # Arrange: un PNG con extensión engañosa
    filename = "radiografia.dcm"
    # Act
    reader = select_reader(filename, png_bytes_sample)
    # Assert
    assert isinstance(reader, RasterReader)


def test_select_reader_detects_dicom_without_extension(dicom_bytes_sample):
    reader = select_reader(None, dicom_bytes_sample)
    assert isinstance(reader, DicomReader)


@pytest.mark.parametrize("filename", ["x.txt", "x.pdf", "x", None])
def test_select_reader_rejects_unknown_formats(filename):
    with pytest.raises(InvalidImageError):
        select_reader(filename, b"contenido cualquiera")


def test_select_reader_rejects_empty_bytes():
    with pytest.raises(InvalidImageError, match="vacío"):
        select_reader("x.png", b"")


@pytest.mark.parametrize("path", SAMPLE_FILES, ids=lambda p: p.name)
def test_read_course_samples(path):
    # Act
    image = read_path(path)
    # Assert
    assert image.pixels.dtype == np.uint8
    assert image.pixels.ndim == 3
    assert image.pixels.shape[2] == 3
    assert image.pixels.max() == 255


@pytest.mark.parametrize(
    "path", [p for p in SAMPLE_FILES if p.suffix == ".dcm"], ids=lambda p: p.name
)
def test_course_dicoms_expose_safe_metadata(path):
    image = read_path(path)
    assert {"age", "sex", "view_position"} <= set(image.metadata)
    assert "PatientID" not in image.metadata
    assert "patient_id" not in image.metadata


def test_dicom_reader_reads_metadata(dicom_bytes_sample):
    image = DicomReader().read(dicom_bytes_sample)
    assert image.metadata["age"] == 45
    assert image.metadata["sex"] == "M"
    assert image.metadata["view_position"] == "PA"
    assert image.source_format == "dicom"


def test_dicom_reader_never_leaks_identifiers(dicom_bytes_sample):
    image = DicomReader().read(dicom_bytes_sample)
    flat = str(image.metadata)
    assert "SECRETO-123" not in flat
    assert "Paciente" not in flat


def test_dicom_monochrome1_is_inverted(gradient_image):
    # Arrange
    normal = DicomReader().read(make_dicom_bytes(gradient_image, "MONOCHROME2"))
    inverted = DicomReader().read(make_dicom_bytes(gradient_image, "MONOCHROME1"))
    # Assert: en MONOCHROME1 el blanco es 0, así que debe invertirse
    np.testing.assert_array_equal(inverted.pixels, 255 - normal.pixels)


def test_dicom_16_bits_is_scaled_to_uint8():
    pixels = np.arange(64 * 64, dtype=np.uint16).reshape(64, 64) * 16
    image = DicomReader().read(make_dicom_bytes(pixels))
    assert image.pixels.dtype == np.uint8
    assert image.pixels.max() == 255


def test_dicom_reader_rejects_garbage():
    with pytest.raises(InvalidImageError):
        DicomReader().read(b"\0" * 128 + b"DICM" + b"basura")


@pytest.mark.parametrize("ext", [".png", ".jpg", ".bmp"])
def test_raster_reader_formats(gradient_image, ext):
    image = RasterReader().read(encode(gradient_image, ext))
    assert image.pixels.shape == (256, 256, 3)
    assert image.metadata == {"rows": 256, "columns": 256}


def test_raster_reader_handles_rgba():
    rgba = np.full((32, 32, 4), 200, dtype=np.uint8)
    image = RasterReader().read(encode(rgba, ".png"))
    assert image.pixels.shape == (32, 32, 3)


def test_raster_reader_rejects_corrupt_png():
    with pytest.raises(InvalidImageError):
        RasterReader().read(b"\x89PNG\r\n\x1a\n" + b"corrupto")


def test_black_image_is_rejected():
    black = np.zeros((32, 32), dtype=np.uint8)
    with pytest.raises(InvalidImageError, match="intensidades"):
        read_image(encode(black, ".png"), "negro.png")


@pytest.mark.parametrize(
    ("values", "expected_max"),
    [([[0, 10], [20, 40]], 255), ([[-5, 0], [5, 10]], 255), ([[1000, 2000], [3000, 4000]], 255)],
)
def test_to_uint8_scales_to_full_range(values, expected_max):
    result = to_uint8(np.array(values))
    assert result.dtype == np.uint8
    assert result.max() == expected_max
    assert result.min() >= 0


def test_to_uint8_rejects_nan():
    with pytest.raises(InvalidImageError):
        to_uint8(np.array([[np.nan, 1.0]]))


@pytest.mark.parametrize("shape", [(8, 8), (8, 8, 3), (8, 8, 4)])
def test_to_three_channels(shape):
    result = to_three_channels(np.ones(shape, dtype=np.uint8))
    assert result.shape == (8, 8, 3)


def test_to_three_channels_rejects_odd_shapes():
    with pytest.raises(InvalidImageError):
        to_three_channels(np.ones((8, 8, 2), dtype=np.uint8))
