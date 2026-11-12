"""Smoke test contra un contenedor en ejecución (paso 4 del README del curso y compuerta de CI).

Uso:  uv run python scripts/container_smoke.py http://localhost:8000
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "artifacts" / "samples" / "person1711_bacteria_4527.jpeg"
EXPECTED = ROOT / "artifacts" / "expected" / "response_example.json"


def main(base_url: str, retries: int = 30) -> int:
    with httpx.Client(base_url=base_url, timeout=120) as client:
        for attempt in range(retries):
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.TransportError:
                pass
            print(f"Esperando el contenedor ({attempt + 1}/{retries})…")
            time.sleep(2)
        else:
            print("✗ /health no respondió", file=sys.stderr)
            return 1
        response = client.post("/predict", files={"file": (SAMPLE.name, SAMPLE.read_bytes())})
        response.raise_for_status()
        body = response.json()
        missing = set(json.loads(EXPECTED.read_text(encoding="utf-8"))) - set(body)
        if missing:
            print(f"✗ faltan claves del contrato: {missing}", file=sys.stderr)
            return 1
        if client.get(body["gradcam_url"]).status_code != 200:
            print("✗ gradcam_url no responde", file=sys.stderr)
            return 1
        bad = client.post("/predict", files={"file": ("x.txt", b"no-imagen")})
        if bad.status_code != 422:
            print(f"✗ entrada inválida devolvió {bad.status_code}", file=sys.stderr)
            return 1
    print(f"✓ contenedor OK: {body['label']} p={body['probability']} · 422 en entrada inválida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"))
