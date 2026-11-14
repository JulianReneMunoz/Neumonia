"""Prototipo · Tomografía: reconstrucción 3D real de pulmones, vía aérea, arterias y lesión.

    make ui-ct        (http://localhost:8502)

Muestra casos ya procesados (`make ct-precompute CT=...`). Si MEDPSeg está configurado
(`NEUMONIA_MEDPSEG_PYTHON`), también permite procesar una tomografía nueva (tarda minutos en CPU).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from neumonia.config import get_settings
from neumonia.controller.ct_service import (
    available_cases,
    build_ct_segmenter,
    load,
    process,
)
from neumonia.view.ct_views import (
    DEFAULT_VISIBLE,
    STYLE,
    figure_3d,
    lobe_rows,
    most_affected_index,
    slice_image,
)

st.set_page_config(page_title="Prototipo · Tomografía 3D", page_icon="🫁", layout="wide")
settings = get_settings()
segmenter = build_ct_segmenter(settings)

st.title("🫁 Prototipo · Tomografía de tórax en 3D")
st.caption(
    "Segmentación automática con MEDPSeg (pulmones, lóbulos, vía aérea, arterias pulmonares, "
    "vidrio esmerilado y consolidación). A diferencia de la radiografía, aquí el 3D es la "
    "anatomía real del paciente, porque la tomografía es un volumen."
)
st.warning(
    "Prototipo en curso, sin validación clínica. No reemplaza la lectura de un radiólogo.",
    icon="⚠️",
)

with st.sidebar:
    st.header("Caso")
    cases = available_cases(settings.ct_cache_dir)
    choice = st.selectbox("Tomografía procesada", list(cases), index=0 if cases else None)
    if segmenter is not None:
        st.divider()
        upload = st.file_uploader("Procesar una tomografía nueva (.nii.gz)", type=["gz", "nii"])
        if upload is not None and st.button("Segmentar (varios minutos en CPU)", type="primary"):
            with tempfile.TemporaryDirectory() as tmp, st.spinner("MEDPSeg trabajando…"):
                path = Path(tmp) / upload.name
                path.write_bytes(upload.getvalue())
                process(path, segmenter, settings.ct_work_dir, settings.ct_cache_dir)
            st.rerun()
    else:
        st.caption("Para procesar tomografías nuevas: `make ct-setup` y NEUMONIA_MEDPSEG_PYTHON.")

if not cases or choice is None:
    st.info("No hay casos procesados. Ejecute `make ct-precompute CT=<archivo.nii.gz>`.")
    st.stop()

case, report = load(cases[choice])
tab_3d, tab_cortes, tab_informe = st.tabs(["🧊 Reconstrucción 3D", "🩻 Cortes", "📋 Informe"])

with tab_3d:
    visible = st.multiselect(
        "Estructuras",
        options=list(STYLE),
        default=list(DEFAULT_VISIBLE),
        format_func=lambda name: STYLE[name][0],
    )
    st.plotly_chart(figure_3d(case.meshes, tuple(visible)), width="stretch")
    st.caption(
        "Vista anterior: el pulmón derecho del paciente queda a la izquierda de la pantalla."
    )

with tab_cortes:
    plane = st.radio("Plano", ["axial", "coronal"], horizontal=True)
    axis = 2 if plane == "axial" else 1
    index = st.slider(
        "Corte",
        0,
        case.labels.shape[axis] - 1,
        most_affected_index(case.labels, plane),
    )
    st.image(
        slice_image(case.ct, case.labels, case.slice_spacing, plane, index),
        caption="Amarillo: vidrio esmerilado · naranja: consolidación · celeste: borde pulmonar",
        width=560,
    )

with tab_informe:
    for line in report.summary:
        st.markdown(f"- {line}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Pulmón comprometido", f"{report.percent_total:.1f} %")
    c2.metric("Volumen de lesión", f"{report.lesion_ml:.0f} mL")
    c3.metric(
        "Severidad tomográfica",
        f"{report.severity_score}/25" if report.severity_score is not None else "—",
    )
    if report.lobes:
        st.table(lobe_rows(report))
