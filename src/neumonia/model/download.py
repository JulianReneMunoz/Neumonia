"""Descarga verificada de los pesos (no se versionan en Git: 118 MB).

Descarga a `.part`, verifica SHA-256 y solo entonces renombra: nunca deja un modelo
a medias ni acepta un archivo alterado (integridad de la cadena de suministro).
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

CHUNK = 1024 * 1024


class ChecksumError(ValueError):
    pass


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download_model(url: str, dest: Path, expected_sha256: str | None) -> Path:
    dest = Path(dest)
    if dest.is_file() and (expected_sha256 is None or sha256_of(dest) == expected_sha256):
        return dest
    if not url.startswith(("https://", "file://")):
        raise ValueError("Solo se permiten URLs https:// o file://")
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as response, partial.open("wb") as handle:  # noqa: S310
        while block := response.read(CHUNK):
            handle.write(block)
    if expected_sha256 is not None and sha256_of(partial) != expected_sha256:
        partial.unlink(missing_ok=True)
        raise ChecksumError("El archivo descargado no coincide con el SHA-256 esperado.")
    partial.replace(dest)
    return dest
