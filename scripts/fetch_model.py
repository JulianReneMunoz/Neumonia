"""Descarga conv_MLP_84.h5 desde el Release público y verifica su SHA-256.

Uso:  uv run python scripts/fetch_model.py   (o `make model`)
"""

from __future__ import annotations

import sys

from neumonia.config import get_settings
from neumonia.model.download import ChecksumError, download_model


def main() -> int:
    settings = get_settings()
    print(f"Modelo → {settings.model_path}")
    try:
        path = download_model(settings.model_url, settings.model_path, settings.model_sha256)
    except ChecksumError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    print(f"✓ listo: {path.name} ({path.stat().st_size / 1e6:.1f} MB, SHA-256 verificado)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
