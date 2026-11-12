"""Clasificador — inversión de dependencias (DIP).

El controlador depende del protocolo `Classifier`, no de Keras. En producción se inyecta
`KerasClassifier`; en las pruebas, un doble falso. Si mañana el modelo pasa a ONNX o a
PyTorch, se escribe otra clase que cumpla el protocolo y nada más cambia.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np

from neumonia.config import CLASS_NAMES


class ModelNotFoundError(FileNotFoundError):
    """El archivo de pesos no existe. Ejecute `make model` para descargarlo."""


@runtime_checkable
class Classifier(Protocol):
    class_names: tuple[str, ...]

    def predict_proba(self, batch: np.ndarray) -> np.ndarray:
        """Recibe (1, H, W, 1) y devuelve un vector de probabilidades (n_clases,)."""
        ...


@lru_cache(maxsize=4)
def load_keras_model(path: str) -> Any:
    """Carga el .h5 una sola vez por proceso (la carga es la operación más costosa)."""
    model_path = Path(path)
    if not model_path.is_file():
        raise ModelNotFoundError(
            f"No existe el modelo en {model_path}. "
            "Ejecute `make model` o defina NEUMONIA_MODEL_PATH."
        )
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf  # import diferido: la app arranca rápido y las pruebas no lo pagan

    return tf.keras.models.load_model(model_path, compile=False)


class KerasClassifier:
    """Adaptador del modelo Keras conv_MLP_84 (entrada 512×512×1, salida softmax de 3 clases)."""

    def __init__(self, model_path: str | Path, class_names: tuple[str, ...] = CLASS_NAMES) -> None:
        self.model_path = Path(model_path)
        self.class_names = class_names
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = load_keras_model(str(self.model_path))
            n_out = int(self._model.outputs[0].shape[-1])
            if n_out != len(self.class_names):
                raise ValueError(
                    f"El modelo tiene {n_out} salidas y se esperaban {len(self.class_names)}."
                )
        return self._model

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def predict_proba(self, batch: np.ndarray) -> np.ndarray:
        output = self.model([batch], training=False)  # el .h5 declara la entrada como lista
        if isinstance(output, list | tuple):
            output = output[0]
        probs = np.asarray(output, dtype=np.float64)[0]
        return probs / probs.sum()
