"""Vista clínica en Streamlit.

Ejecutar: `make ui`  (uv run streamlit run src/neumonia/view/streamlit_app.py)

Solo dibuja widgets: la lógica de formato está en `presenter.py` y la inferencia en el
controlador, al que se llega por una `PredictionGateway` (local o HTTP).
"""

from __future__ import annotations

import streamlit as st

from neumonia.config import get_settings
from neumonia.controller.errors import GatewayError, InvalidImageError, ModelNotFoundError
from neumonia.controller.gateways import build_gateway
from neumonia.controller.report import DISCLAIMER, append_history, build_pdf_report
from neumonia.view.overlays import zones_overlay
from neumonia.view.presenter import (
    patient_rows,
    present,
    present_findings,
    validate_patient_id,
)
from neumonia.view.visual3d import attention_surface_figure, lungs_3d_figure

st.set_page_config(page_title="Apoyo al diagnóstico de neumonía", page_icon="🫁", layout="wide")
settings = get_settings()


@st.cache_resource(show_spinner="Cargando el modelo…")
def gateway():
    return build_gateway(settings)


st.title("🫁 Apoyo al diagnóstico de neumonía")
st.caption("Radiografía de tórax (DICOM, JPG o PNG) · Modelo conv_MLP_84 · Explicabilidad Grad-CAM")
st.warning(DISCLAIMER, icon="⚠️")

with st.sidebar:
    st.header("Paciente")
    patient_id = st.text_input("Documento del paciente", max_chars=15)
    uploaded = st.file_uploader("Radiografía", type=["dcm", "jpg", "jpeg", "png"])
    run = st.button("Predecir", type="primary", disabled=uploaded is None, width="stretch")
    patient_panel = st.container()
    st.divider()
    mode = "API REST" if settings.api_url else "local"
    st.caption(f"Modo de inferencia: **{mode}** · {settings.model_version}")

if run and uploaded is not None:
    error = validate_patient_id(patient_id)
    if error:
        st.error(error)
    else:
        try:
            with st.spinner("Analizando la radiografía…"):
                st.session_state["result"] = gateway().predict(uploaded.getvalue(), uploaded.name)
                st.session_state["patient"] = patient_id.strip()
                st.session_state["filename"] = uploaded.name
        except InvalidImageError as exc:
            st.error(f"Imagen inválida: {exc}")
        except ModelNotFoundError as exc:
            st.error(str(exc))
        except GatewayError as exc:
            st.error(f"No fue posible consultar la API: {exc}")

result = st.session_state.get("result")
if result is not None:
    with patient_panel:
        st.divider()
        st.subheader("Datos del paciente")
        for label, value in patient_rows(
            result.prediction.metadata,
            st.session_state.get("patient", ""),
            st.session_state.get("filename", ""),
        ):
            st.markdown(f"**{label}:** {value}")
    view = present(result.prediction)
    findings = result.prediction.findings
    tab_res, tab_inf, tab_3d = st.tabs(["🩻 Resultado", "📋 Informe detallado", "🧊 Vista 3D"])

    with tab_res:
        col_img, col_cam, col_res = st.columns([1, 1, 1])
        col_img.subheader("Radiografía")
        col_img.image(result.original_rgb, width="stretch")
        col_cam.subheader("Grad-CAM")
        if result.prediction.heatmap is not None:
            col_cam.image(result.prediction.heatmap, width="stretch")
        col_res.subheader("Resultado")
        col_res.markdown(f"### :{view.color}[{view.headline}]")
        col_res.metric("Probabilidad", view.probability_text)
        col_res.write(f"**Subtipo sugerido:** {view.subtype_text}")
        col_res.table(
            {"Clase": list(view.probabilities), "Probabilidad": list(view.probabilities.values())}
        )

    with tab_inf:
        if findings is None:
            st.info("El informe detallado requiere el mapa Grad-CAM, que no está disponible.")
        else:
            fv = present_findings(findings)
            st.subheader("Informe de hallazgos asistido")
            for line in fv.summary:
                st.markdown(f"- {line}")
            if fv.shortcut_warning:
                st.warning(
                    "Posible atajo del modelo: atiende tanto o más fuera de los pulmones "
                    "que dentro.",
                    icon="⚠️",
                )
            m1, m2, m3 = st.columns(3)
            m1.metric("Lateralidad", fv.laterality)
            m2.metric("Extensión de alta atención", fv.extent)
            m3.metric("Atención fuera de los pulmones", fv.outside)
            col_zonas, col_tabla = st.columns([2, 3])
            if findings.lung_grid:
                col_zonas.image(
                    zones_overlay(result.original_rgb, findings.lung_grid, findings.dominant_zone),
                    caption=(
                        f"{fv.segmentation}: azul = pulmón derecho, verde = izquierdo, "
                        "naranja = zona dominante"
                    ),
                    width="stretch",
                )
            col_tabla.table(
                {
                    "Zona pulmonar": [z for z, _, _ in fv.zone_rows],
                    "Atención media": [v for _, v, _ in fv.zone_rows],
                    "Dominante": ["◀" if d else "" for _, _, d in fv.zone_rows],
                }
            )

    with tab_3d:
        if findings is None or not findings.attention_grid:
            st.info("La vista 3D requiere el mapa Grad-CAM, que no está disponible.")
        else:
            st.caption(
                "Una radiografía es una imagen 2D: estas vistas no reconstruyen el pulmón en 3D. "
                "Muestran en relieve dónde se fijó el modelo y su atención por zona "
                "pulmonar aproximada."
            )
            g1, g2 = st.columns(2)
            g1.plotly_chart(
                attention_surface_figure(result.original_rgb, findings.attention_grid),
                width="stretch",
            )
            g2.plotly_chart(lungs_3d_figure(findings.zone_attention), width="stretch")

    patient = st.session_state.get("patient", "anonimo")
    c1, c2 = st.columns(2)
    if c1.button("💾 Guardar en historial", width="stretch"):
        path = append_history(settings.history_path, patient, result.prediction)
        st.success(f"Guardado en {path.name}.")
    c2.download_button(
        "📄 Descargar reporte PDF",
        data=build_pdf_report(
            result.prediction, result.original_rgb, patient, settings.model_version
        ),
        file_name=f"reporte_{patient}.pdf",
        mime="application/pdf",
        width="stretch",
    )
