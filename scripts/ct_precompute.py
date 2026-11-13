"""Procesa tomografías con MEDPSeg y deja el caso listo para la demo (`make ui-ct`).

Uso:
  make ct-precompute CT=data/raw/ct/coronacases_001.nii.gz
  uv run --extra ct python scripts/ct_precompute.py --ct <archivo.nii.gz> [--spacing 1.5]
  uv run --extra ct python scripts/ct_precompute.py --from-output <carpeta MEDPSeg> --case <id> \
      [--ct-image <tomografía original>]

`--from-output` reutiliza resultados de MEDPSeg ya calculados (por ejemplo en otra máquina con GPU).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from neumonia.config import get_settings
from neumonia.controller.ct_service import cache_segmentation, load, process
from neumonia.model.ct_segmentation import MedpsegSegmenter, load_medpseg_output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ct", type=Path, nargs="*", default=[])
    parser.add_argument("--from-output", type=Path, default=None)
    parser.add_argument("--case", default=None)
    parser.add_argument("--ct-image", type=Path, default=None, help="tomografía original (cortes)")
    parser.add_argument("--spacing", type=float, default=1.5, help="mm; 0 = resolución original")
    parser.add_argument("--medpseg-python", type=Path, default=None)
    args = parser.parse_args()
    settings = get_settings()

    paths: list[Path] = []
    if args.from_output is not None:
        if not args.case:
            print("✗ Con --from-output indique --case <id>.")
            return 1
        ct_file = args.ct_image or args.from_output / f"{args.case}.nii.gz"
        seg = load_medpseg_output(args.from_output, args.case, ct_file)
        paths.append(cache_segmentation(seg, settings.ct_cache_dir))
    python = args.medpseg_python or settings.medpseg_python
    if args.ct and python is None:
        print("✗ Falta MEDPSeg: ejecute `make ct-setup` y configure NEUMONIA_MEDPSEG_PYTHON.")
        return 1
    for ct in args.ct:
        start = time.time()
        print(f"Segmentando {ct.name} con MEDPSeg (CPU: varios minutos)...")
        segmenter = MedpsegSegmenter(python, spacing=args.spacing)
        paths.append(process(ct, segmenter, settings.ct_work_dir, settings.ct_cache_dir))
        print(f"  listo en {time.time() - start:.0f} s")
    for path in paths:
        _, report = load(path)
        print(f"✓ {path}")
        print(json.dumps({k: report.to_dict()[k] for k in ("percent_total", "severity_score")}))
    if not paths:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
