"""Panel «Datos del paciente» de la barra lateral: lenguaje claro y sin identificadores."""

from __future__ import annotations

import numpy as np

from neumonia.controller.gateways import GatewayResult
from neumonia.domain import Label, Prediction
from neumonia.view.app import VIEW_DIR
from neumonia.view.presenter import patient_rows


def test_dicom_metadata_is_shown_in_plain_language():
    # Arrange
    metadata = {
        "age": 25,
        "sex": "F",
        "view_position": "AP",
        "modality": "DX",
        "body_part": "CHEST",
        "rows": 3480,
        "columns": 4240,
        "patient_code": "PAC-7F3A91C2",
        "dataset_code": "COVID-19-AR-16434363",
    }
    # Act
    rows = dict(patient_rows(metadata, " 1144123456 ", "radiografia_16434363.dcm"))
    # Assert
    assert rows["Documento"] == "1144123456"
    assert rows["Código del paciente"] == "PAC-7F3A91C2"
    assert rows["Código en el dataset"] == "COVID-19-AR-16434363"
    assert rows["Edad"] == "25 años"
    assert rows["Sexo"] == "Femenino"
    assert rows["Proyección"] == "AP (anteroposterior)"
    assert rows["Modalidad"] == "Radiografía digital (DX)"
    assert rows["Región"] == "Tórax"
    assert rows["Imagen"] == "4240 × 3480 px"
    assert rows["Archivo"] == "radiografia_16434363.dcm"


def test_jpg_without_metadata_says_so_and_unknown_values_pass_through():
    # Arrange
    unknown = {"view_position": "ll", "modality": "XA", "body_part": "abdomen"}
    # Act
    jpg = dict(patient_rows({}, "", "muestra.jpeg"))
    other = dict(patient_rows(unknown))
    # Assert
    assert jpg["Documento"] == "No ingresado"
    assert jpg["Metadatos"].startswith("No disponibles")
    assert jpg["Archivo"] == "muestra.jpeg"
    assert other["Proyección"] == "Lateral"
    assert other["Modalidad"] == "XA"
    assert other["Región"] == "Abdomen"
    assert "Archivo" not in other


def test_identifying_fields_are_never_shown():
    # Arrange
    metadata = {"age": 40, "PatientName": "Paciente^Prueba", "PatientID": "SECRETO-123"}
    # Act
    text = str(patient_rows(metadata, "12345"))
    # Assert
    assert "SECRETO" not in text
    assert "Prueba" not in text


def test_sidebar_shows_patient_data_after_a_prediction(tmp_path, monkeypatch):
    # Arrange
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("NEUMONIA_HISTORY_PATH", str(tmp_path / "historial.csv"))
    app = AppTest.from_file(str(VIEW_DIR / "streamlit_app.py"), default_timeout=60)
    prediction = Prediction(
        label=Label.NORMAL,
        probability=0.8,
        subtype="normal",
        class_probabilities={"bacteriana": 0.0, "normal": 0.8, "viral": 0.2},
        heatmap=None,
        metadata={"age": 25, "sex": "F", "view_position": "AP", "modality": "DX"},
    )
    app.session_state["result"] = GatewayResult(prediction, np.zeros((8, 8, 3), np.uint8))
    app.session_state["patient"] = "1144123456"
    app.session_state["filename"] = "radiografia.dcm"
    # Act
    app.run()
    # Assert
    assert not app.exception
    sidebar = [m.value for m in app.sidebar.markdown]
    assert "**Edad:** 25 años" in sidebar
    assert "**Sexo:** Femenino" in sidebar
    assert "**Documento:** 1144123456" in sidebar
