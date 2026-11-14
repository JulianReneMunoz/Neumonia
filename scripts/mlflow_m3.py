"""MLflow del M3 (SPEC-013): 3 corridas comparables + Model Registry del modelo que usa el backend.

Requisito: el servidor de MLflow corriendo en otra terminal (`make mlflow`, http://127.0.0.1:5050).

Uso:
  make mlflow-runs        # RSNA (200 imágenes) si está; si no, muestras del aula
  uv run --group mlops python scripts/mlflow_m3.py --source course --no-register  # rápido

Corridas (mismo experimento `neumonia-m3`, mismo modelo conv_MLP_84@modelo-v1, mismas imágenes):
  1. baseline-umbral-0.50   2. umbral-0.30   3. sin-clahe-umbral-0.50
Nunca registra PatientID ni PatientName: solo el nombre del archivo y las probabilidades.
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from neumonia.config import PROJECT_ROOT, get_settings
from neumonia.model.classifier import KerasClassifier
from neumonia.tracking.m3_runs import (
    RUNS,
    LabeledImage,
    RunResult,
    confusion,
    course_items,
    run_config,
    sample_items,
)

RSNA_CSV = PROJECT_ROOT / "data" / "rsna" / "rsna_eval_500.csv"
RSNA_DIR = PROJECT_ROOT / "data" / "raw" / "rsna"
COURSE_ZIPS = (PROJECT_ROOT / "data" / "DICOM.zip", PROJECT_ROOT / "data" / "JPG.zip")
REGISTERED_NAME = "neumonia-conv-mlp-84"
LICENSE_TAG = "Pesos del caso base UAO-Neumonía (Release modelo-v1): solo uso académico"


def rsna_items() -> list[LabeledImage]:
    print(f"Indexando DICOM en {RSNA_DIR} ...", flush=True)
    index = {p.stem: p for p in RSNA_DIR.rglob("*.dcm")}
    items = []
    with RSNA_CSV.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            path = index.get((row.get("SOPInstanceUID") or "").strip())
            if path is not None and str(row.get("target", "")).strip() in {"0", "1"}:
                items.append(LabeledImage(path, int(row["target"]), row.get("label", "")))
    return items


def course_dir() -> Path:
    import zipfile

    out = Path(tempfile.gettempdir()) / "neumonia_muestras_aula"
    for archive in COURSE_ZIPS:
        if archive.is_file():
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(out)
    return out


def check_server(uri: str) -> None:
    if not uri.startswith("http"):
        return
    try:
        urllib.request.urlopen(f"{uri.rstrip('/')}/health", timeout=5)  # noqa: S310 - URI local
    except OSError:
        sys.exit(f"No hay servidor MLflow en {uri}. Ejecute `make mlflow` en otra terminal.")


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"


def write_artifacts(result: RunResult, folder: Path, dataset: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "predicciones.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result.rows[0]))
        writer.writeheader()
        writer.writerows(result.rows)
    (tn, fp), (fn, tp) = confusion(result.rows)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow([[tn, fp], [fn, tp]], cmap="Reds")
        for (i, j), v in {(0, 0): tn, (0, 1): fp, (1, 0): fn, (1, 1): tp}.items():
            ax.text(j, i, str(v), ha="center", va="center", fontsize=14)
        ax.set_xticks([0, 1], ["Pred. normal", "Pred. neumonía"])
        ax.set_yticks([0, 1], ["Real normal", "Real neumonía"])
        ax.set_title(result.config.name)
        fig.tight_layout()
        fig.savefig(folder / "matriz_confusion.png", dpi=120)
        plt.close(fig)
    except ImportError:
        pass
    m = result.metrics
    lines = [
        f"# {result.config.name}",
        "",
        result.config.description,
        "",
        f"- Dataset: {dataset} · n = {int(m['n'])} · omitidas = {result.skipped}",
        f"- Umbral: {result.config.threshold} · Preprocesamiento: {result.config.preprocessing}",
        f"- Matriz [[TN, FP], [FN, TP]] = [[{tn}, {fp}], [{fn}, {tp}]]",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        *[f"| {k} | {v:.4f} |" for k, v in sorted(m.items())],
    ]
    (folder / "reporte.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def register_model(mlflow, model_path: Path, threshold: float, run_name: str) -> str:
    from mlflow.tracking import MlflowClient

    from neumonia.tracking.pyfunc_model import NeumoniaPyfunc

    kwargs = {
        "python_model": NeumoniaPyfunc(threshold),
        "artifacts": {"keras_model": str(model_path)},
        "registered_model_name": REGISTERED_NAME,
        "pip_requirements": ["tensorflow-cpu", "opencv-python-headless", "pydicom", "pandas"],
    }
    try:
        info = mlflow.pyfunc.log_model(name="modelo", **kwargs)  # MLflow 3
    except TypeError:
        info = mlflow.pyfunc.log_model(artifact_path="modelo", **kwargs)  # MLflow 2
    version = str(info.registered_model_version)
    client = MlflowClient()
    client.set_registered_model_alias(REGISTERED_NAME, "produccion", version)
    client.update_registered_model(
        REGISTERED_NAME,
        description=(
            "conv_MLP_84@modelo-v1 (Keras, 3 clases: bacteriana/normal/viral) servido por la API "
            "FastAPI del proyecto. Alias `produccion` = versión que usa el backend. Uso académico."
        ),
    )
    for key, value in {
        "model_version": get_settings().model_version,
        "stage": "Production",
        "run": run_name,
    }.items():
        client.set_model_version_tag(REGISTERED_NAME, version, key, value)
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", choices=["auto", "rsna", "course"], default="auto")
    parser.add_argument("--limit", type=int, default=200, help="Imágenes de RSNA (0 = todas).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--experiment", default="neumonia-m3")
    parser.add_argument(
        "--tracking-uri", default=os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5050")
    )
    parser.add_argument("--no-register", action="store_true", help="No registrar el modelo.")
    args = parser.parse_args()

    source = args.source
    if source == "auto":
        source = "rsna" if RSNA_CSV.is_file() and RSNA_DIR.is_dir() else "course"
    if source == "rsna":
        items = sample_items(rsna_items(), args.limit or None, args.seed)
        dataset = f"RSNA adjudicado (rsna_eval_500.csv), n={len(items)}, semilla {args.seed}"
    else:
        items = course_items(course_dir())
        dataset = f"Muestras del aula (data/DICOM.zip + data/JPG.zip), n={len(items)}"
    if not items:
        sys.exit("No hay imágenes etiquetadas para evaluar.")
    positives = sum(i.target for i in items)
    print(f"{dataset}: {positives} con neumonía, {len(items) - positives} sin neumonía.")

    check_server(args.tracking_uri)
    import mlflow

    mlflow.set_tracking_uri(args.tracking_uri)
    experiment = mlflow.set_experiment(args.experiment)
    settings = get_settings()
    classifier = KerasClassifier(settings.model_path)
    classifier.model  # noqa: B018 - carga una vez, fuera de la medición de latencia
    import tensorflow as tf

    backend = f"CPU · TensorFlow {tf.__version__} · {platform.system()}"
    commit = git_commit()
    results = []
    for config in RUNS:
        print(f"→ {config.name} ...", flush=True)
        result = run_config(classifier.predict_proba, items, config)
        results.append(result)
        with mlflow.start_run(run_name=config.name) as run:
            mlflow.log_params(
                {
                    "model": settings.model_version,
                    "model_sha256": settings.model_sha256,
                    "threshold": config.threshold,
                    "clahe": config.clahe,
                    "preprocessing": config.preprocessing,
                    "dataset": dataset,
                    "n_images": len(items),
                    "seed": args.seed,
                    "backend": backend,
                    "python": platform.python_version(),
                }
            )
            mlflow.log_metrics(result.metrics)
            mlflow.set_tags(
                {
                    "licencia": LICENSE_TAG,
                    "equipo": "Grupo 8",
                    "ambiente": "dev",
                    "commit": commit,
                    "spec": "SPEC-013",
                    "mlflow.note.content": config.description,
                }
            )
            with tempfile.TemporaryDirectory() as tmp:
                write_artifacts(result, Path(tmp), dataset)
                mlflow.log_artifacts(tmp, artifact_path="evaluacion")
            if config is RUNS[0] and not args.no_register:
                print("  registrando el modelo en el Model Registry (copia el .h5) ...", flush=True)
                version = register_model(
                    mlflow, settings.model_path, config.threshold, run.info.run_name
                )
                print(f"  {REGISTERED_NAME} v{version} → alias «produccion»")

    print()
    cols = ["exact.", "sens.", "espec.", "F1", "AUC"]
    print(f"{'corrida':<24}" + "".join(f"{c:>8}" for c in cols) + f"{'p95 ms':>9}")
    for r in results:
        m = r.metrics
        print(
            f"{r.config.name:<24}{m.get('accuracy', 0):>8.3f}{m.get('recall', 0):>8.3f}"
            f"{m.get('specificity', 0):>8.3f}{m.get('f1', 0):>8.3f}{m.get('roc_auc', 0):>8.3f}"
            f"{m['latency_p95_ms']:>9.1f}"
        )
    print(f"\nComparar en {args.tracking_uri}/#/experiments/{experiment.experiment_id}")


if __name__ == "__main__":
    main()
