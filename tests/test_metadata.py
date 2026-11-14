"""Metadatos DICOM: parseo de edad/sexo, grupos etarios y minimización de datos."""

from __future__ import annotations

import pytest

from neumonia.model.metadata import (
    FORBIDDEN_FIELDS,
    age_group,
    extract_metadata,
    normalize_sex,
    parse_age,
    pseudonym,
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
    assert meta == {
        "age": 30,
        "sex": "F",
        "view_position": "AP",
        "rows": 1024,
        "patient_code": pseudonym("123"),
    }
    assert not (set(meta) & {f.lower() for f in FORBIDDEN_FIELDS})
    assert "123" not in meta["patient_code"]


def test_extract_metadata_skips_blank_values():
    assert extract_metadata({"PatientAge": "", "ViewPosition": "  "}) == {}


def test_pseudonym_is_stable_secret_dependent_and_hides_the_id(monkeypatch):
    code = pseudonym("1144123456", key="clave-a")
    assert code == pseudonym(" 1144123456 ", key="clave-a")
    assert code.startswith("PAC-")
    assert len(code) == 12
    assert code != pseudonym("1144123457", key="clave-a")
    assert code != pseudonym("1144123456", key="clave-b")
    assert "1144123456" not in code
    monkeypatch.setenv("NEUMONIA_PSEUDONYM_KEY", "clave-a")
    assert pseudonym("1144123456") == code


def test_dataset_code_only_when_the_dicom_declares_it_anonymized():
    public = {"PatientID": "COVID-19-AR-16434363", "PatientIdentityRemoved": "YES"}
    hospital = {"PatientID": "1144123456", "PatientIdentityRemoved": "NO"}
    meta_public = extract_metadata(public)
    meta_hospital = extract_metadata(hospital)
    assert meta_public["dataset_code"] == "COVID-19-AR-16434363"
    assert "dataset_code" not in meta_hospital
    assert "1144123456" not in str(meta_hospital)
    assert meta_public["patient_code"].startswith("PAC-")
