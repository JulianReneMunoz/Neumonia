"""Instala MEDPSeg en su propio entorno para el prototipo de tomografía (ADR-0010).

Uso:  make ct-setup        (≈ 1 GB de pesos + PyTorch; una sola vez)

1. Clona MEDPSeg (MIT, MICLab-Unicamp) en un commit fijo.
2. Descarga sus pesos (`data_poly.zip`, 768 MB) y verifica el SHA-256.
3. Crea `.medpseg/env` con uv (Python 3.13) e instala MEDPSeg ahí, aislado del proyecto.
Al final indica el valor de NEUMONIA_MEDPSEG_PYTHON.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from neumonia.config import PROJECT_ROOT
from neumonia.model.ct_segmentation import python_in_env

REPO = "https://github.com/MICLab-Unicamp/medpseg"
COMMIT = "1e6617dc0f9e853596bea69a28787c76efa15b35"
WEIGHTS_URL = f"{REPO}/releases/download/v4.0.0/data_poly.zip"
WEIGHTS_SHA256 = "b0890cd477997469707fe679f2f9d6ab848458058351d53f9ac05276436cd659"
HOME = PROJECT_ROOT / ".medpseg"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd: list[str]) -> None:
    print("→", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    if shutil.which("git") is None or shutil.which("uv") is None:
        print("✗ Se necesitan git y uv en el PATH.")
        return 1
    repo = HOME / "repo"
    if not (repo / ".git").is_dir():
        run(["git", "clone", REPO, str(repo)])
    run(["git", "-C", str(repo), "checkout", "-q", COMMIT])

    weights = HOME / "data_poly.zip"
    if not weights.is_file() or sha256_of(weights) != WEIGHTS_SHA256:
        print("Descargando pesos de MEDPSeg (768 MB)...")
        urllib.request.urlretrieve(WEIGHTS_URL, weights)  # noqa: S310 - URL fija (GitHub)
    if sha256_of(weights) != WEIGHTS_SHA256:
        print(f"✗ SHA-256 inesperado en {weights}; bórrelo y repita.")
        return 1
    with zipfile.ZipFile(weights) as archive:
        archive.extractall(repo / "medpseg")

    env = HOME / "env"
    if not python_in_env(env).is_file():
        run(["uv", "venv", "-p", "3.13", str(env)])
    run(["uv", "pip", "install", "--python", str(python_in_env(env)), str(repo)])
    print(f"\n✓ MEDPSeg listo. Configure:\n  NEUMONIA_MEDPSEG_PYTHON={python_in_env(env)}")
    print('  PowerShell: $env:NEUMONIA_MEDPSEG_PYTHON="' + str(python_in_env(env)) + '"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
