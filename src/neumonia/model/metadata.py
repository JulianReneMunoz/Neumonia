"""Extracción de metadatos DICOM útiles y NO identificables.

Solo se exponen campos demográficos y técnicos agregados (edad, sexo, proyección...).
Nunca se devuelven PatientID, PatientName, fechas ni instituciones (minimización de datos,
Ley 1581 de 2012 en Colombia y art. 10 del EU AI Act sobre gobernanza de datos).
"""

from __future__ import annotations

import re
from typing import Any

SAFE_FIELDS: dict[str, str] = {
    "PatientAge": "age",
    "PatientSex": "sex",
    "ViewPosition": "view_position",
    "Modality": "modality",
    "BodyPartExamined": "body_part",
    "PhotometricInterpretation": "photometric",
    "Rows": "rows",
    "Columns": "columns",
}

FORBIDDEN_FIELDS: frozenset[str] = frozenset(
    {
        "PatientID",
        "PatientName",
        "PatientBirthDate",
        "InstitutionName",
        "ReferringPhysicianName",
        "StudyDate",
        "AccessionNumber",
    }
)

_AGE_PATTERN = re.compile(r"^\s*(\d{1,3})\s*([DWMY]?)\s*$", re.IGNORECASE)
_AGE_FACTORS = {"": 1.0, "Y": 1.0, "M": 1 / 12, "W": 1 / 52, "D": 1 / 365}


def parse_age(raw: Any) -> int | None:
    """Convierte la edad DICOM ('059Y', '6', '018M') a años enteros. None si no es válida."""
    if raw is None:
        return None
    match = _AGE_PATTERN.match(str(raw))
    if not match:
        return None
    value = int(match.group(1)) * _AGE_FACTORS[match.group(2).upper()]
    years = int(value)
    return years if 0 <= years <= 120 else None


def normalize_sex(raw: Any) -> str | None:
    value = str(raw).strip().upper() if raw is not None else ""
    return value if value in {"M", "F", "O"} else None


def age_group(age: int | None) -> str:
    """Grupo etario para análisis por subgrupos (equidad del modelo)."""
    if age is None:
        return "desconocido"
    if age < 18:
        return "0-17"
    if age < 40:
        return "18-39"
    if age < 65:
        return "40-64"
    return "65+"


def extract_metadata(dataset: Any) -> dict[str, Any]:
    """Extrae los campos permitidos de un `pydicom.Dataset` (o cualquier objeto con `.get`)."""
    out: dict[str, Any] = {}
    for dicom_key, name in SAFE_FIELDS.items():
        value = dataset.get(dicom_key, None)
        if value is None or str(value).strip() == "":
            continue
        if dicom_key == "PatientAge":
            age = parse_age(value)
            if age is not None:
                out[name] = age
        elif dicom_key == "PatientSex":
            sex = normalize_sex(value)
            if sex is not None:
                out[name] = sex
        elif dicom_key in {"Rows", "Columns"}:
            out[name] = int(value)
        else:
            out[name] = str(value).strip()
    return out
