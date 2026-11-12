"""Lectura de radiografías — patrón Estrategia.

Cada formato es una estrategia (`DicomReader`, `RasterReader`) con la misma interfaz
(`ImageReader`). `select_reader` elige la estrategia por extensión y, si falla, por la
firma binaria del archivo. Agregar un formato nuevo (p. ej. NIfTI) es agregar una clase,
sin modificar el controlador (principio abierto/cerrado).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Protocol, runtime_checkable

import cv2
import numpy as np
import pydicom
from pydicom.errors import InvalidDicomError

from neumonia.domain import RadiographImage
from neumonia.model.metadata import extract_metadata


class InvalidImageError(ValueError):
    """La entrada no es una radiografía legible (vacía, corrupta o formato no soportado)."""


@runtime_checkable
class ImageReader(Protocol):
    extensions: tuple[str, ...]

    def can_read(self, data: bytes) -> bool: ...

    def read(self, data: bytes) -> RadiographImage: ...


def to_uint8(array: np.ndarray) -> np.ndarray:
    """Escala a 0-255 como el monolito original: max(x, 0) / max * 255."""
    values = np.asarray(array, dtype=np.float64)
    values = np.maximum(values, 0)
    peak = values.max() if values.size else 0
    if not np.isfinite(peak) or peak <= 0:
        raise InvalidImageError("La imagen está vacía o no tiene intensidades positivas.")
    return np.uint8(values / peak * 255.0)


def to_three_channels(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    if array.ndim == 3 and array.shape[2] == 4:
        return cv2.cvtColor(array, cv2.COLOR_BGRA2BGR)
    if array.ndim == 3 and array.shape[2] == 3:
        return array
    raise InvalidImageError(f"Forma de imagen no soportada: {array.shape}")


class DicomReader:
    """Lee DICOM (.dcm) con pydicom; maneja MONOCHROME1 y profundidades de 8/12/16 bits."""

    extensions: tuple[str, ...] = (".dcm", ".dicom")

    def can_read(self, data: bytes) -> bool:
        return len(data) > 132 and data[128:132] == b"DICM"

    def read(self, data: bytes) -> RadiographImage:
        try:
            dataset = pydicom.dcmread(io.BytesIO(data), force=True)
            pixels = dataset.pixel_array
        except (InvalidDicomError, AttributeError, ValueError, TypeError, KeyError) as exc:
            raise InvalidImageError(f"DICOM ilegible: {exc}") from exc
        if pixels.ndim == 3 and pixels.shape[-1] not in (3, 4):
            pixels = pixels[0]  # multiframe: se usa el primer cuadro
        image = to_uint8(pixels)
        if str(dataset.get("PhotometricInterpretation", "")).upper() == "MONOCHROME1":
            image = 255 - image
        return RadiographImage(
            pixels=to_three_channels(image),
            source_format="dicom",
            metadata=extract_metadata(dataset),
        )


class RasterReader:
    """Lee JPG/PNG/BMP con OpenCV (canal BGR, como el monolito original)."""

    extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp")
    _SIGNATURES: tuple[bytes, ...] = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"BM")

    def can_read(self, data: bytes) -> bool:
        return any(data.startswith(sig) for sig in self._SIGNATURES)

    def read(self, data: bytes) -> RadiographImage:
        buffer = np.frombuffer(data, dtype=np.uint8)
        decoded = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED) if buffer.size else None
        if decoded is None:
            raise InvalidImageError("No se pudo decodificar la imagen JPG/PNG.")
        image = to_uint8(decoded)
        height, width = image.shape[:2]
        return RadiographImage(
            pixels=to_three_channels(image),
            source_format="raster",
            metadata={"rows": int(height), "columns": int(width)},
        )


DEFAULT_READERS: tuple[ImageReader, ...] = (DicomReader(), RasterReader())


def select_reader(
    filename: str | None, data: bytes, readers: tuple[ImageReader, ...] = DEFAULT_READERS
) -> ImageReader:
    """Elige la estrategia: primero por firma binaria (fiable), luego por extensión."""
    if not data:
        raise InvalidImageError("El archivo está vacío.")
    for reader in readers:
        if reader.can_read(data):
            return reader
    suffix = Path(filename or "").suffix.lower()
    for reader in readers:
        if suffix in reader.extensions:
            return reader
    raise InvalidImageError(
        f"Formato no soportado ({suffix or 'sin extensión'}). Use DICOM, JPG o PNG."
    )


def read_image(
    data: bytes, filename: str | None = None, readers: tuple[ImageReader, ...] = DEFAULT_READERS
) -> RadiographImage:
    return select_reader(filename, data, readers).read(data)


def read_path(path: str | Path) -> RadiographImage:
    path = Path(path)
    return read_image(path.read_bytes(), path.name)
