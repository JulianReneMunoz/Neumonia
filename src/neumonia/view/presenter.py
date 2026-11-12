"""Presentador de la vista: lógica de formato sin Streamlit (probable con pytest).

Mantener la vista "tonta" (Humble Object) permite probar todo lo que decide qué se
muestra, dejando en `streamlit_app.py` solo la disposición de los widgets.
"""

from __future__ import annotations

from dataclasses import dataclass

from neumonia.domain import Label, Prediction

METADATA_LABELS = {
    "age": "Edad (años)",
    "sex": "Sexo",
    "view_position": "Proyección",
    "modality": "Modalidad",
    "body_part": "Región",
    "photometric": "Fotometría",
    "rows": "Alto (px)",
    "columns": "Ancho (px)",
}
SUBTYPE_LABELS = {"bacteriana": "Bacteriana", "viral": "Viral", "normal": "Sin hallazgos"}


@dataclass(frozen=True)
class ResultView:
    headline: str
    color: str
    probability_text: str
    subtype_text: str
    probabilities: dict[str, str]
    metadata_rows: list[tuple[str, str]]


def format_probability(value: float) -> str:
    return f"{max(0.0, min(1.0, float(value))) * 100:.2f}%"


def present(prediction: Prediction) -> ResultView:
    is_pneumonia = prediction.label is Label.PNEUMONIA
    return ResultView(
        headline="Hallazgos compatibles con NEUMONÍA"
        if is_pneumonia
        else "Sin hallazgos de neumonía",
        color="red" if is_pneumonia else "green",
        probability_text=format_probability(prediction.probability),
        subtype_text=SUBTYPE_LABELS.get(prediction.subtype, prediction.subtype),
        probabilities={
            SUBTYPE_LABELS.get(k, k): format_probability(v)
            for k, v in prediction.class_probabilities.items()
        },
        metadata_rows=[(METADATA_LABELS.get(k, k), str(v)) for k, v in prediction.metadata.items()],
    )


def validate_patient_id(raw: str) -> str | None:
    """Devuelve un mensaje de error o None si el documento es válido (solo dígitos, 5-15)."""
    value = raw.strip()
    if not value:
        return "Ingrese el documento del paciente."
    if not value.isdigit() or not 5 <= len(value) <= 15:
        return "El documento debe tener entre 5 y 15 dígitos."
    return None
