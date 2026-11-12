#!/usr/bin/env python3
"""Smoke test del caso Neumonía (sección 5 del README del curso).

1. Carga el modelo.  2. Infiere sobre cada muestra de artifacts/samples/.
3. Valida el JSON contra artifacts/expected/response_example.json.

Uso:  uv run python smoke_infer.py      (o `make smoke`)
No evalúa exactitud: verifica que el artefacto carga, infiere y cumple el contrato.
"""

from __future__ import annotations

import json
from pathlib import Path

from neumonia.config import get_settings
from neumonia.controller.factory import build_service

BASE = Path(__file__).resolve().parent
SAMPLES = BASE / "artifacts" / "samples"
EXPECTED = BASE / "artifacts" / "expected" / "response_example.json"


def main() -> int:
    settings = get_settings()
    if not settings.model_path.exists():
        raise SystemExit(f"Falta el modelo: {settings.model_path}. Ejecute `make model`.")
    expected_keys = set(json.loads(EXPECTED.read_text(encoding="utf-8")))
    service = build_service(settings)
    samples = sorted(
        p for p in SAMPLES.iterdir() if p.suffix.lower() in {".dcm", ".jpeg", ".jpg", ".png"}
    )
    for path in samples:
        prediction = service.predict_bytes(path.read_bytes(), path.name)
        payload = prediction.to_contract("/static/gradcam/smoke.png", settings.model_version)
        missing = expected_keys - set(payload)
        assert not missing, f"Faltan claves del contrato: {missing}"
        assert prediction.heatmap is not None
        assert prediction.heatmap.shape == (512, 512, 3)
        label, prob, subtype = payload["label"], payload["probability"], payload["subtype"]
        print(f"✓ {path.name:<36} {label:<9} p={prob:.3f} ({subtype})")
    print(f"✓ modelo {settings.model_path.name} · {len(samples)} muestras · contrato OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
