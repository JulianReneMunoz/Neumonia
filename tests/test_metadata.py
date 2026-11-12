"""Metadatos DICOM: parseo de edad/sexo, grupos etarios y minimización de datos."""

from __future__ import annotations

import pytest

from neumonia.model.metadata import (
    FORBIDDEN_FIELDS,
    age_group,
    extract_metadata,
    normalize_sex,
    parse_age,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("059Y", 59),
        ("6", 6),
        ("018M", 1),
        ("104W", 2),
        ("400D", 1),
        (" 45 ", 45),
        ("045y", 45),
        (None, None),
        ("", None),
        ("abc", None),
        ("999Y", None),
    ],
)
def test_parse_age(raw, expected):
    assert parse_age(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("M", "M"), ("f", "F"), (" O ", "O"), ("X", None), (None, None), ("", None)],
)
def test_normalize_sex(raw, expected):
    assert normalize_sex(raw) == expected


@pytest.mark.parametrize(
    ("age", "group"),
    [
        (None, "desconocido"),
        (0, "0-17"),
        (17, "0-17"),
        (18, "18-39"),
        (39, "18-39"),
        (40, "40-64"),
        (64, "40-64"),
        (65, "65+"),
        (90, "65+"),
    ],
)
def test_age_group(age, group):
    assert age_group(age) == group


def test_extract_metadata_keeps_only_safe_fields():
    # Arrange: una cabecera con identificadores personales
    header = {
        "PatientID": "123",
        "PatientName": "Ana",
        "PatientAge": "030Y",
        "PatientSex": "F",
        "ViewPosition": "AP",
        "Rows": 1024,
        "InstitutionName": "Clínica",
    }
    # Act
    meta = extract_metadata(header)
    # Assert
    assert meta == {"age": 30, "sex": "F", "view_position": "AP", "rows": 1024}
    assert not (set(meta) & {f.lower() for f in FORBIDDEN_FIELDS})


def test_extract_metadata_skips_blank_values():
    assert extract_metadata({"PatientAge": "", "ViewPosition": "  "}) == {}
