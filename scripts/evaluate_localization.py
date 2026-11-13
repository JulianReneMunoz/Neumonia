"""¿Grad-CAM apunta a la lesión? Compara el mapa con las cajas de radiólogos de RSNA (fase 2).

Uso:
  make evaluate-loc                                   # 300 casos con neumonía, registra en MLflow
  uv run --group mlops python scripts/evaluate_localization.py --limit 300
  uv run --group mlops python scripts/evaluate_localization.py \
      --labels data/processed/rsna_boxes.csv --images data/raw/rsna_adjudicado

--labels acepta el CSV de Kaggle (patientId) o la exportación adjudicada (SOPInstanceUID).
--images es la carpeta con los DICOM (se busca en subcarpetas; el nombre del archivo es la clave).

Con NEUMONIA_LUNG_SEGMENTER=pspnet la alerta de atajo usa la silueta pulmonar real (ADR-0008).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from neumonia.config import PROJECT_ROOT, get_settings
from neumonia.controller.factory import build_service
from neumonia.evaluation_localization import build_cases, evaluate_localization
from neumonia.tracking.tracker import build_tracker

RSNA = PROJECT_ROOT / "data" / "raw" / "rsna"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", type=Path, default=RSNA / "stage_2_train_labels.csv")
    parser.add_argument("--images", type=Path, default=RSNA / "stage_2_train_images")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "runtime" / "localizacion")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()

    if not args.labels.is_file():
        print(f"✗ No se encontró {args.labels}. Descargue RSNA (make dataset-rsna) o use --labels.")
        return 1
    cases = build_cases(args.labels, args.images, limit=args.limit, seed=args.seed)
    if not cases:
        print(f"✗ Ningún caso con cajas tiene su DICOM en {args.images}.")
        return 1
    settings = get_settings()
    tracker = build_tracker(
        None if args.no_mlflow else settings.mlflow_tracking_uri,
        tags={"model_version": settings.model_version, "experimento": "localizacion"},
    )
    result = evaluate_localization(
        build_service(settings),
        cases,
        tracker,
        args.out,
        params={
            "model_version": settings.model_version,
            "lung_segmenter": settings.lung_segmenter,
            "seed": args.seed,
        },
    )
    print(json.dumps(result.summary, indent=2))
    print(f"Omitidos: {result.skipped} · Resultados en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
