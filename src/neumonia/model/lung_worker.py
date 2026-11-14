"""Proceso aislado de segmentación pulmonar: `python -m neumonia.model.lung_worker módulo:fábrica`.

TensorFlow y `torchvision` no pueden convivir en un mismo proceso (abortan con
"LLVM ERROR: inconsistency in registered CommandLine options"). Este proceso hijo carga solo
PyTorch, construye el segmentador una vez y atiende peticiones por stdin/stdout con mensajes
pickle de longitud prefijada. Nunca importa TensorFlow.

El canal es privado entre el proceso principal y su hijo (no se expone a la red).
"""

from __future__ import annotations

import importlib
import os
import pickle
import struct
import sys
from typing import IO, Any

HEADER = struct.Struct("!Q")


def write_frame(stream: IO[bytes], payload: Any) -> None:
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    stream.write(HEADER.pack(len(data)) + data)
    stream.flush()


def read_frame(stream: IO[bytes]) -> Any:
    header = stream.read(HEADER.size)
    if len(header) < HEADER.size:
        raise EOFError("El canal se cerró.")
    size = HEADER.unpack(header)[0]
    data = stream.read(size)
    if len(data) < size:
        raise EOFError("Mensaje incompleto.")
    return pickle.loads(data)  # noqa: S301 - canal privado con el proceso padre


def load_factory(spec: str):
    module_name, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module_name), attr)


def serve(spec: str, inbox: IO[bytes], outbox: IO[bytes]) -> None:
    try:
        segmenter = load_factory(spec)()
    except Exception as exc:  # se informa al padre en cada petición
        segmenter, startup_error = None, f"{type(exc).__name__}: {exc}"
    else:
        startup_error = ""
    while True:
        try:
            pixels, size = read_frame(inbox)
        except EOFError:
            return
        if segmenter is None:
            write_frame(outbox, ("error", startup_error))
            continue
        try:
            write_frame(outbox, ("ok", segmenter.segment(pixels, size)))
        except Exception as exc:
            write_frame(outbox, ("error", f"{type(exc).__name__}: {exc}"))


def main() -> None:  # pragma: no cover - se ejecuta en el proceso hijo
    outbox = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # descargas y prints de librerías → stderr
    sys.stdout = sys.stderr
    serve(sys.argv[1], sys.stdin.buffer, outbox)


if __name__ == "__main__":  # pragma: no cover
    main()
