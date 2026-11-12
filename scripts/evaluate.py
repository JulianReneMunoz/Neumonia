"""Evalúa el modelo sobre un catálogo de metadatos y registra el experimento en MLflow.

Uso:
  uv run --group mlops python scripts/evaluate.py --metadata data/processed/course_metadata.csv
  uv run --group mlops python scripts/evaluate.py \
      --metadata data/processed/rsna_metadata.csv --limit 500
  uv run --group mlops mlflow ui        # http://127.0.0.1:5000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from neumonia.config import PROJECT_ROOT, get_settings
from neumonia.controller.factory import build_service
from neumonia.data.dataset import Sample, read_metadata_csv
from neumonia.evaluation import evaluate
from neumonia.tracking.tracker import build_tracker


def rows_to_samples(rows: list[dict[str, str]]) -> list[Sample]:
    samples = []
    for row in rows:
        metadata = {k: row[k] for k in ("sex", "view_position") if row.get(k)}
        if row.get("age"):
            metadata["age"] = int(row["age"])
        samples.append(
            Sample(
                image_path=row["image_path"],
                source=row["source"],
                target=int(row["target"]),
                subtype=row.get("subtype", ""),
                metadata=metadata,
            )
        )
    return samples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "runtime" / "evaluation")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    samples = rows_to_samples(read_metadata_csv(args.metadata))[: args.limit]
    tracker = build_tracker(
        None if args.no_mlflow else settings.mlflow_tracking_uri,
        tags={"model_version": settings.model_version, "dataset": args.metadata.stem},
    )
    result = evaluate(
        build_service(settings),
        samples,
        tracker,
        args.out,
        params={"model_version": settings.model_version, "dataset": args.metadata.name},
    )
    print(json.dumps(result.metrics, indent=2))
    print(f"Omitidas: {result.skipped} · Resultados en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
