"""Envoltura `mlflow.pyfunc` de conv_MLP_84 para el Model Registry (SPEC-013).

Recibe una lista de rutas de imagen (DICOM/JPG/PNG) y devuelve las probabilidades por clase y la
decisión. Usa el mismo lector, preprocesamiento y política que el backend, para que el modelo
registrado sea el que realmente sirve la API. Solo se importa desde `scripts/mlflow_m3.py`.
"""

from __future__ import annotations

from typing import Any

import mlflow.pyfunc


class NeumoniaPyfunc(mlflow.pyfunc.PythonModel):
    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def load_context(self, context: Any) -> None:
        from neumonia.model.classifier import KerasClassifier

        self.classifier = KerasClassifier(context.artifacts["keras_model"])

    def predict(self, context: Any, model_input: Any, params: dict | None = None) -> Any:
        import pandas as pd

        from neumonia.config import CLASS_NAMES, NORMAL_INDEX
        from neumonia.model.preprocessing import preprocess
        from neumonia.model.readers import read_path

        paths = (
            model_input["path"].tolist() if hasattr(model_input, "columns") else list(model_input)
        )
        rows = []
        for path in paths:
            probs = self.classifier.predict_proba(preprocess(read_path(path).pixels))
            p_pneumonia = 1.0 - float(probs[NORMAL_INDEX])
            rows.append(
                {
                    **{f"p_{n}": float(p) for n, p in zip(CLASS_NAMES, probs, strict=True)},
                    "p_pneumonia": p_pneumonia,
                    "label": "PNEUMONIA" if p_pneumonia >= self.threshold else "NORMAL",
                }
            )
        return pd.DataFrame(rows)
