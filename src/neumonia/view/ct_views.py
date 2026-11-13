"""Vistas del prototipo de tomografía (ADR-0010): reconstrucción 3D, cortes e informe.

Funciones puras (Plotly + numpy, sin Streamlit ni cv2) para poder probarlas.
A diferencia de la radiografía, aquí el 3D **sí es la anatomía del paciente**: sale de un volumen.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go

STYLE = {
    "pulmon_derecho": ("Pulmón derecho", "#8ecae6", 0.12),
    "pulmon_izquierdo": ("Pulmón izquierdo", "#8ecae6", 0.12),
    "via_aerea": ("Vía aérea", "#f1f1f1", 0.85),
    "vasos": ("Arterias pulmonares", "#d1495b", 0.45),
    "vidrio_esmerilado": ("Vidrio esmerilado", "#ffd166", 0.9),
    "consolidacion": ("Consolidación", "#f3722c", 0.95),
}
DEFAULT_VISIBLE = tuple(STYLE)
OVERLAY = {2: ((255, 209, 102), 0.55), 3: ((243, 114, 44), 0.7)}
LUNG_EDGE = (142, 202, 230)


def figure_3d(meshes: dict[str, Any], visible: tuple[str, ...] = DEFAULT_VISIBLE) -> go.Figure:
    """Mallas (`vertices`, `faces`) en mm, RAS+; vista anterior: el derecho queda a la izquierda."""
    traces = []
    for name in STYLE:
        mesh = meshes.get(name)
        if name not in visible or mesh is None or len(mesh.faces) == 0:
            continue
        label, color, opacity = STYLE[name]
        v, f = mesh.vertices, mesh.faces
        traces.append(
            go.Mesh3d(
                x=v[:, 0],
                y=v[:, 1],
                z=v[:, 2],
                i=f[:, 0],
                j=f[:, 1],
                k=f[:, 2],
                color=color,
                opacity=opacity,
                name=label,
                showlegend=True,
                flatshading=False,
                lighting={"ambient": 0.45, "diffuse": 0.8, "specular": 0.3, "roughness": 0.6},
                hovertemplate=f"{label}<extra></extra>",
            )
        )
    annotations = []
    for name, text in (("pulmon_derecho", "DERECHO"), ("pulmon_izquierdo", "IZQUIERDO")):
        mesh = meshes.get(name)
        if mesh is not None and len(mesh.vertices):
            center = mesh.vertices.mean(axis=0)
            top = mesh.vertices[:, 2].max()
            annotations.append(
                {
                    "x": float(center[0]),
                    "y": float(center[1]),
                    "z": float(top + 15),
                    "text": text,
                    "showarrow": False,
                    "font": {"size": 12, "color": "#e8e8e8"},
                }
            )
    figure = go.Figure(data=traces)
    figure.update_layout(
        height=680,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor="#11151c",
        legend={"font": {"color": "#e8e8e8"}, "bgcolor": "rgba(0,0,0,0)"},
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "zaxis": {"visible": False},
            "aspectmode": "data",
            "bgcolor": "#11151c",
            "annotations": annotations,
            "camera": {"eye": {"x": 0.0, "y": 1.9, "z": 0.25}, "up": {"x": 0, "y": 0, "z": 1}},
        },
    )
    return figure


def _orient(plane: np.ndarray, row_mm: float, col_mm: float) -> np.ndarray:
    """(x, otro) → imagen con el derecho del paciente a la izquierda y lo anterior/superior arriba,
    corrigiendo la relación de aspecto si los vóxeles no son cúbicos."""
    image = plane.T[::-1, ::-1]
    if abs(row_mm - col_mm) > 1e-6:
        rows = np.clip(
            np.round(np.arange(int(image.shape[0] * row_mm / col_mm)) * col_mm / row_mm).astype(
                int
            ),
            0,
            image.shape[0] - 1,
        )
        image = image[rows]
    return image


def _edges(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1)
    inner = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    return mask & ~inner


def slice_image(
    ct: np.ndarray | None,
    labels: np.ndarray,
    spacing: tuple[float, float, float],
    plane: str,
    index: int,
) -> np.ndarray:
    """Corte axial o coronal en RGB uint8 con la lesión superpuesta y el borde pulmonar."""
    if plane not in ("axial", "coronal"):
        raise ValueError("plane debe ser 'axial' o 'coronal'.")
    if plane == "axial":
        index = int(np.clip(index, 0, labels.shape[2] - 1))
        lab = _orient(labels[:, :, index], spacing[1], spacing[0])
        base = ct[:, :, index] if ct is not None else None
        base = _orient(base, spacing[1], spacing[0]) if base is not None else None
    else:
        index = int(np.clip(index, 0, labels.shape[1] - 1))
        lab = _orient(labels[:, index, :], spacing[2], spacing[0])
        base = ct[:, index, :] if ct is not None else None
        base = _orient(base, spacing[2], spacing[0]) if base is not None else None
    gray = base if base is not None else np.where(lab > 0, 90, 20).astype(np.uint8)
    rgb = np.repeat(gray[..., None], 3, axis=2).astype(np.float64)
    for value, (color, alpha) in OVERLAY.items():
        sel = lab == value
        rgb[sel] = (1 - alpha) * rgb[sel] + alpha * np.asarray(color, dtype=np.float64)
    rgb[_edges(lab > 0)] = LUNG_EDGE
    return np.clip(rgb, 0, 255).astype(np.uint8)


def most_affected_index(labels: np.ndarray, plane: str) -> int:
    """Corte con más lesión (o el del centro si no hay lesión)."""
    axis = 2 if plane == "axial" else 1
    other = tuple(a for a in range(3) if a != axis)
    lesion = (labels >= 2).sum(axis=other)
    return int(np.argmax(lesion)) if lesion.any() else labels.shape[axis] // 2


def lobe_rows(report: Any) -> dict[str, list[Any]]:
    from neumonia.controller.ct_analysis import LOBE_LABELS

    return {
        "Lóbulo": [LOBE_LABELS.get(lobe.name, lobe.name) for lobe in report.lobes],
        "Volumen (mL)": [f"{lobe.volume_ml:.0f}" for lobe in report.lobes],
        "Comprometido": [f"{lobe.percent:.1f} %" for lobe in report.lobes],
        "Puntaje (0–5)": [lobe.score for lobe in report.lobes],
    }
