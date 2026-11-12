"""Descarga / prepara el dataset y genera el catálogo de metadatos.

Fuentes:
  course   Descomprime data/JPG.zip y data/DICOM.zip (sin internet).
  rsna     RSNA Pneumonia Detection Challenge 2018 vía Kaggle (≈3.9 GB, DICOM + metadatos).
  kermany  Chest X-Ray Images (Pneumonia) de Kermany et al. vía Kaggle (≈1.2 GB, JPG).

Para rsna/kermany se necesita una cuenta de Kaggle:
  1. Kaggle → Settings → API → "Create New Token" → guarde kaggle.json en
     %USERPROFILE%\\.kaggle\\kaggle.json (Windows) o ~/.kaggle/kaggle.json.
  2. Solo RSNA: acepte las reglas en
     https://www.kaggle.com/competitions/rsna-pneumonia-detection-challenge/rules

Uso:
  uv run python scripts/fetch_dataset.py --source course
  uv run python scripts/fetch_dataset.py --source rsna [--subset 2000]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from neumonia.config import PROJECT_ROOT
from neumonia.data.dataset import (
    extract_course_zips,
    load_rsna,
    scan_folder,
    stratified_subset,
    summarize,
    write_metadata_csv,
)

RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"
KAGGLE = {
    "rsna": ["competitions", "download", "-c", "rsna-pneumonia-detection-challenge"],
    "kermany": ["datasets", "download", "-d", "paultimothymooney/chest-xray-pneumonia"],
}


def kaggle_download(source: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.glob("*.csv")) or any(dest.glob("chest_xray")):
        print(f"✓ {source} ya está en {dest}")
        return
    runner = ["uvx", "kaggle"] if shutil.which("uvx") else ["kaggle"]
    print(f"Descargando {source} con Kaggle CLI (puede tardar varios minutos)…")
    subprocess.run([*runner, *KAGGLE[source], "-p", str(dest)], check=True)
    for archive in dest.glob("*.zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
        archive.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--source", choices=["course", "rsna", "kermany"], default="course")
    parser.add_argument(
        "--subset", type=int, default=None, help="Submuestra estratificada de N imágenes"
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.source == "course":
        root = extract_course_zips(PROJECT_ROOT / "data", RAW / "course")
        samples = scan_folder(root, source="course")
    elif args.source == "rsna":
        root = RAW / "rsna"
        try:
            kaggle_download("rsna", root)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"✗ Falló la descarga: {exc}. Revise kaggle.json y las reglas.", file=sys.stderr)
            return 1
        samples = load_rsna(root)
    else:
        root = RAW / "kermany"
        try:
            kaggle_download("kermany", root)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"✗ Falló la descarga: {exc}", file=sys.stderr)
            return 1
        samples = scan_folder(root / "chest_xray" / "test", source="kermany")

    if args.subset:
        samples = stratified_subset(samples, args.subset, seed=args.seed)
    out = write_metadata_csv(samples, PROCESSED / f"{args.source}_metadata.csv")
    summary = summarize(samples)
    (PROCESSED / f"{args.source}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"✓ {len(samples)} imágenes catalogadas → {out.relative_to(PROJECT_ROOT)}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
