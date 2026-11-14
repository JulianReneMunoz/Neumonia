"""Visualizaciones 3D interactivas (Plotly) para la vista clínica.

Una radiografía es una proyección 2D: no contiene profundidad. Por eso estas vistas NO reconstruyen
el pulmón en 3D (eso requeriría tomografía). Son dos representaciones honestas:

1. `attention_surface_figure`: relieve 3D del mapa de atención (Grad-CAM) sobre la radiografía;
   la altura y el color indican cuánto influyó cada región en la decisión.
2. `lungs_3d_figure`: esquema 3D de ambos pulmones dividido en 6 zonas (superior, media e inferior
   de cada lado), coloreado según la atención media del modelo en cada zona.

Funciones puras (sin Streamlit) → se prueban con pytest.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from neumonia.view.presenter import ZONE_DISPLAY

BASE_SIZE = 128  # resolución de la radiografía usada como "piso" del relieve
RELIEF_HEIGHT = 120.0


def _to_gray(original_rgb: np.ndarray, size: int = BASE_SIZE) -> np.ndarray:
    image = np.asarray(original_rgb, dtype=np.float64)
    gray = image.mean(axis=2) if image.ndim == 3 else image
    rows = np.linspace(0, gray.shape[0] - 1, size).astype(int)
    cols = np.linspace(0, gray.shape[1] - 1, size).astype(int)
    return gray[np.ix_(rows, cols)]


def attention_surface_figure(
    original_rgb: np.ndarray, attention_grid: list[list[float]]
) -> go.Figure:
    """Relieve 3D: la radiografía en el piso (z=0) y el Grad-CAM como superficie elevada."""
    gray = _to_gray(original_rgb)
    cam = np.clip(np.asarray(attention_grid, dtype=np.float64), 0.0, 1.0)
    if cam.ndim != 2 or cam.size == 0:
        raise ValueError("attention_grid debe ser una matriz 2D no vacía.")

    extent = 512.0
    bx = np.linspace(0, extent, gray.shape[1])
    by = np.linspace(0, extent, gray.shape[0])
    cx = np.linspace(0, extent, cam.shape[1])
    cy = np.linspace(0, extent, cam.shape[0])

    base = go.Surface(
        x=bx,
        y=by,
        z=np.zeros_like(gray),
        surfacecolor=gray,
        colorscale="Gray",
        showscale=False,
        name="Radiografía",
        hoverinfo="skip",
    )
    relief = go.Surface(
        x=cx,
        y=cy,
        z=cam * RELIEF_HEIGHT,
        surfacecolor=cam,
        colorscale="Jet",
        cmin=0.0,
        cmax=1.0,
        opacity=0.85,
        name="Atención (Grad-CAM)",
        colorbar={"title": "Atención", "len": 0.6},
        hovertemplate="atención: %{surfacecolor:.0%}<extra></extra>",
    )
    figure = go.Figure(data=[base, relief])
    figure.update_layout(
        title="Relieve 3D de la atención del modelo sobre la radiografía",
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False, "autorange": "reversed"},
            "zaxis": {"title": "atención", "range": [0, RELIEF_HEIGHT * 1.1]},
            "aspectratio": {"x": 1, "y": 1, "z": 0.45},
            "camera": {"eye": {"x": 1.2, "y": -1.5, "z": 1.1}},
        },
        height=520,
    )
    return figure


def _ellipsoid(center_x: float, rx: float, ry: float, rz: float, n: int = 48):
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = center_x + rx * np.outer(np.cos(u), np.sin(v))
    y = ry * np.outer(np.sin(u), np.sin(v))
    z = rz * np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def _zone_color(z: np.ndarray, rz: float, side: str, scores: dict[str, float]) -> np.ndarray:
    third = rz / 3.0
    levels = np.where(z > third, "superior", np.where(z > -third, "medio", "inferior"))
    lookup = np.vectorize(lambda level: scores.get(f"{side}_{level}", 0.0))
    return lookup(levels).astype(np.float64)


def lungs_3d_figure(zone_attention: dict[str, float]) -> go.Figure:
    """Esquema 3D de los pulmones por zonas (no anatómico). Pulmón derecho a la izquierda,
    como en una radiografía frontal."""
    scores = {k: float(v) for k, v in zone_attention.items()}
    cmax = max(0.25, max(scores.values(), default=0.0))
    traces = []
    for side, center, rx, label in (
        ("derecho", -1.15, 0.95, "Pulmón derecho"),
        ("izquierdo", 1.15, 0.85, "Pulmón izquierdo"),
    ):
        rz, ry = 2.0, 0.8
        x, y, z = _ellipsoid(center, rx, ry, rz)
        color = _zone_color(z, rz, side, scores)
        traces.append(
            go.Surface(
                x=x,
                y=y,
                z=z,
                surfacecolor=color,
                colorscale="YlOrRd",
                cmin=0.0,
                cmax=cmax,
                showscale=side == "izquierdo",
                colorbar={"title": "Atención media", "len": 0.6, "tickformat": ".0%"},
                name=label,
                hovertemplate=f"{label}<br>atención: %{{surfacecolor:.0%}}<extra></extra>",
            )
        )
    annotations = []
    for zone, value in scores.items():
        side, level = zone.split("_")
        x = -1.15 if side == "derecho" else 1.15
        z = {"superior": 1.35, "medio": 0.0, "inferior": -1.35}[level]
        annotations.append(
            {
                "x": x,
                "y": -0.95,
                "z": z,
                "text": f"{ZONE_DISPLAY.get(zone, zone)}: {value:.0%}",
                "showarrow": False,
                "font": {"size": 11, "color": "black"},
                "bgcolor": "rgba(255,255,255,0.75)",
            }
        )
    figure = go.Figure(data=traces)
    figure.update_layout(
        title="Atención del modelo por zona pulmonar (esquema 3D, no anatómico)",
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "zaxis": {"visible": False},
            "aspectmode": "data",
            "annotations": annotations,
            "camera": {"eye": {"x": 0.0, "y": -2.2, "z": 0.4}},
        },
        height=520,
    )
    return figure
