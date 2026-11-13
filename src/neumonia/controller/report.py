"""Reporte PDF e historial CSV (funciones del monolito, ahora sin capturas de pantalla).

El original usaba `tkcap`/`pyautogui` para fotografiar la ventana: no funciona en un
servidor ni en Docker. Aquí el PDF se genera desde los datos con fpdf2.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from fpdf import FPDF
from PIL import Image

from neumonia.controller.findings import ZONE_LABELS
from neumonia.domain import Findings, Prediction

HISTORY_HEADER = ("fecha_utc", "paciente", "label", "probabilidad", "subtipo")
DISCLAIMER = (
    "Herramienta académica de apoyo. No reemplaza el criterio de un profesional de la salud "
    "ni constituye un dispositivo médico certificado."
)


def png_bytes(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()


def sanitize_patient_id(patient_id: str) -> str:
    cleaned = "".join(ch for ch in str(patient_id).strip() if ch.isalnum() or ch in "-_")
    return cleaned[:32] or "anonimo"


def append_history(path: Path, patient_id: str, prediction: Prediction) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(HISTORY_HEADER)
        writer.writerow(
            [
                datetime.now(UTC).isoformat(timespec="seconds"),
                sanitize_patient_id(patient_id),
                prediction.label.value,
                f"{prediction.probability:.4f}",
                prediction.subtype,
            ]
        )
    return path


def _latin1(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf_report(
    prediction: Prediction,
    original_rgb: np.ndarray,
    patient_id: str,
    model_version: str,
) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(
        0, 10, _latin1("Reporte de apoyo al diagnóstico de neumonía"), new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font("Helvetica", "", 10)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    for line in (
        f"Paciente: {sanitize_patient_id(patient_id)}",
        f"Fecha: {stamp}",
        f"Modelo: {model_version}",
        f"Resultado: {prediction.label.value} ({prediction.probability:.1%})",
        f"Subtipo sugerido: {prediction.subtype}",
        "Probabilidades: "
        + ", ".join(f"{k}={v:.1%}" for k, v in prediction.class_probabilities.items()),
    ):
        pdf.cell(0, 6, _latin1(line), new_x="LMARGIN", new_y="NEXT")
    if prediction.metadata:
        meta = ", ".join(f"{k}={v}" for k, v in prediction.metadata.items())
        pdf.multi_cell(0, 6, _latin1(f"Metadatos: {meta}"), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 4
    pdf.image(io.BytesIO(png_bytes(original_rgb)), x=10, y=y, w=90, h=90)
    if prediction.heatmap is not None:
        pdf.image(io.BytesIO(png_bytes(prediction.heatmap)), x=110, y=y, w=90, h=90)
    pdf.set_y(y + 94)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(95, 5, "Radiografia", align="C")
    pdf.cell(95, 5, "Grad-CAM", align="C", new_x="LMARGIN", new_y="NEXT")
    if prediction.findings is not None:
        _write_findings(pdf, prediction.findings)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, _latin1(DISCLAIMER))
    return bytes(pdf.output())


def _write_findings(pdf: FPDF, findings: Findings) -> None:
    """Informe detallado: narrativa + tabla de atención por zona pulmonar."""
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _latin1("Informe de hallazgos asistido"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for line in findings.summary:
        pdf.multi_cell(0, 5, _latin1(f"- {line}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    kind = "silueta segmentada" if findings.lung_source == "pspnet" else "aproximada"
    pdf.cell(110, 6, _latin1(f"Zona pulmonar ({kind})"), border=1)
    pdf.cell(40, 6, _latin1("Atención media"), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for zone, value in findings.zone_attention.items():
        marker = "  <- dominante" if zone == findings.dominant_zone else ""
        pdf.cell(110, 6, _latin1(ZONE_LABELS.get(zone, zone) + marker), border=1)
        pdf.cell(40, 6, f"{value:.0%}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        6,
        _latin1(
            f"Extensión de alta atención: {findings.extent_pct:.0f} %  ·  "
            f"Atención fuera de los pulmones: {findings.out_of_lung_pct:.0f} %"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
