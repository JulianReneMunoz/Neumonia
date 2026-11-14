"""Descarga y verifica los pesos de PSPNet (TorchXRayVision) para la segmentación pulmonar.

Uso:  make seg   (instala el extra `seg` y ejecuta este script)
Los pesos (~273 MB) quedan en ~/.torchxrayvision/models_data/ y se verifican con SHA-256.
"""

from __future__ import annotations

import sys

from neumonia.model.lung_segmentation import PSPNET_SHA256, sha256_of, weights_path


def main() -> int:
    try:
        import torchxrayvision as xrv
    except ImportError:
        print("✗ Falta el extra de segmentación. Ejecute: uv sync --all-groups --extra seg")
        return 1
    path = weights_path()
    if not path.exists():
        print("Descargando PSPNet (TorchXRayVision, ~273 MB)...")
        xrv.baseline_models.chestx_det.PSPNet()
    digest = sha256_of(path)
    if digest != PSPNET_SHA256:
        print(f"✗ SHA-256 inesperado en {path}: {digest}. Bórrelo y repita `make seg`.")
        return 1
    print(f"✓ PSPNet verificada (SHA-256 {digest[:12]}…) en {path}")
    print("  Activar: $env:NEUMONIA_LUNG_SEGMENTER='pspnet' (PowerShell) o `make ui-seg`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
