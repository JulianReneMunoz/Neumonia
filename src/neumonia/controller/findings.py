"""Informe de hallazgos en lenguaje natural (regla de negocio de comunicación clínica).

Redacta frases prudentes a partir de la decisión y del análisis de atención. Nunca afirma un
diagnóstico: describe la sugerencia del modelo, dónde miró y con qué limitaciones.
"""

from __future__ import annotations

from dataclasses import replace

from neumonia.domain import Findings, Label

ZONE_LABELS = {
    "derecho_superior": "campo superior del pulmón derecho",
    "derecho_medio": "campo medio del pulmón derecho",
    "derecho_inferior": "campo inferior del pulmón derecho",
    "izquierdo_superior": "campo superior del pulmón izquierdo",
    "izquierdo_medio": "campo medio del pulmón izquierdo",
    "izquierdo_inferior": "campo inferior del pulmón izquierdo",
}
LATERALITY_LABELS = {
    "derecho": "predominio en el pulmón derecho",
    "izquierdo": "predominio en el pulmón izquierdo",
    "bilateral": "distribución bilateral",
    "sin_foco": "sin un foco de atención definido",
}
SUBTYPE_LABELS = {"bacteriana": "bacteriano", "viral": "viral"}
NOTE = (
    "Las regiones indican dónde se fijó el modelo (Grad-CAM); no son una segmentación de lesiones "
    "ni reemplazan la lectura de un radiólogo."
)


def describe(findings: Findings, label: Label, probability: float, subtype: str) -> list[str]:
    lines: list[str] = []
    if label is Label.PNEUMONIA:
        origin = SUBTYPE_LABELS.get(subtype)
        kind = f" de probable patrón {origin}" if origin else ""
        lines.append(
            f"El modelo sugiere hallazgos compatibles con neumonía{kind} "
            f"(probabilidad {probability:.1%})."
        )
    else:
        lines.append(
            f"El modelo no sugiere hallazgos compatibles con neumonía (probabilidad de normalidad "
            f"{probability:.1%})."
        )
    zone = ZONE_LABELS.get(findings.dominant_zone, findings.dominant_zone)
    if findings.dominant_zone and findings.laterality == "sin_foco":
        lines.append(
            "La atención del modelo dentro de los pulmones es difusa, sin un foco definido; "
            f"el valor más alto está en el {zone}."
        )
    elif findings.dominant_zone:
        lines.append(
            f"La región que más influyó en la decisión se ubica en el {zone}, con "
            f"{LATERALITY_LABELS.get(findings.laterality, findings.laterality)}."
        )
    if findings.dominant_zone:
        area = "segmentada" if findings.lung_source == "pspnet" else "aproximada"
        lines.append(
            "Extensión estimada de la región de alta atención: "
            f"{findings.extent_pct:.0f} % del área pulmonar {area}."
        )
    if findings.lung_source == "pspnet":
        lines.append(
            "Zonas calculadas sobre la silueta pulmonar segmentada automáticamente "
            "(PSPNet, TorchXRayVision); revise que el contorno coincida con los pulmones."
        )
    elif findings.lung_note:
        lines.append(findings.lung_note)
    if findings.shortcut_warning:
        lines.append(
            "Advertencia de calidad: el modelo atiende tanto o más fuera de los campos pulmonares "
            f"(razón {findings.outside_inside_ratio:.2f}; "
            f"{findings.out_of_lung_pct:.0f} % de la atención) que dentro: marcadores, bordes o "
            "dispositivos. El resultado puede deberse a un atajo del "
            "modelo; interprételo con cautela."
        )
    lines.append(NOTE)
    return lines


def with_summary(findings: Findings, label: Label, probability: float, subtype: str) -> Findings:
    return replace(findings, summary=describe(findings, label, probability, subtype))
