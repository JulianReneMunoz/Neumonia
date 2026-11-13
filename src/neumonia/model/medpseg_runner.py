"""Ejecuta MEDPSeg sin interfaz gráfica, DENTRO del entorno de MEDPSeg (ADR-0010).

Uso (lo invoca `MedpsegSegmenter`, no se importa desde la app):
    <python-de-medpseg> medpseg_runner.py <tomografia.nii.gz> <carpeta_salida> [--spacing 1.5]

Solo usa la biblioteca estándar, SimpleITK y medpseg (todos presentes en ese entorno). El comando
`medpseg_cpu` original importa Tkinter para su GUI y falla en servidores; aquí se llama al pipeline
directamente. `--spacing` remuestrea a vóxeles isotrópicos para bajar memoria y tiempo en CPU
(0 = usar la resolución original).
"""

from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
from pathlib import Path


def resample(src: Path, dst: Path, spacing: float) -> Path:  # pragma: no cover - entorno MEDPSeg
    import SimpleITK as sitk  # noqa: N813 - alias habitual de la biblioteca

    image = sitk.ReadImage(str(src))
    old_spacing = image.GetSpacing()
    if all(abs(s - spacing) < 0.05 for s in old_spacing):
        return src
    old_size = image.GetSize()
    new_size = [max(1, round(n * s / spacing)) for n, s in zip(old_size, old_spacing, strict=True)]
    resampled = sitk.Resample(
        image,
        new_size,
        sitk.Transform(),
        sitk.sitkLinear,
        image.GetOrigin(),
        (spacing,) * 3,
        image.GetDirection(),
        -1024,
        image.GetPixelID(),
    )
    sitk.WriteImage(resampled, str(dst))
    return dst


def main() -> int:  # pragma: no cover - se ejecuta en el entorno de MEDPSeg
    parser = argparse.ArgumentParser()
    parser.add_argument("ct", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--spacing", type=float, default=1.5)
    parser.add_argument("--no-lobes", action="store_true")
    args = parser.parse_args()

    from medpseg.pipeline import pipeline

    args.output.mkdir(parents=True, exist_ok=True)
    case_id = args.ct.name.replace(".nii.gz", "").replace(".nii", "")
    source = args.ct
    if args.spacing > 0:
        source = resample(args.ct, args.output / f"{case_id}.nii.gz", args.spacing)

    messages: queue.Queue = queue.Queue()

    def relay() -> None:
        while True:
            item = messages.get()
            if item is None:  # MEDPSeg avisa el fin con None
                return
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "write":
                print(item[1], flush=True)

    threading.Thread(target=relay, daemon=True).start()
    start = time.time()
    pipeline(
        runlist=[str(source)],
        batch_size=1,
        output_path=str(args.output),
        display=False,
        info_q=messages,
        cpu=True,
        windows_itksnap_path="",
        linux_itksnap_path="",
        debug=False,
        act=False,
        post=True,
        lobe_seg=not args.no_lobes,
        cli=True,
    )
    time.sleep(0.5)
    print(f"MEDPSEG_OK {time.time() - start:.0f} s", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
