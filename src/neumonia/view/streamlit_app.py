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
from neumonia.view.presenter import present, validate_patient_id

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
    run = st.button("Predecir", type="primary", disabled=uploaded is None, use_container_width=True)
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
        except InvalidImageError as exc:
            st.error(f"Imagen inválida: {exc}")
        except ModelNotFoundError as exc:
            st.error(str(exc))
        except GatewayError as exc:
            st.error(f"No fue posible consultar la API: {exc}")

result = st.session_state.get("result")
if result is not None:
    view = present(result.prediction)
    col_img, col_cam, col_res = st.columns([1, 1, 1])
    col_img.subheader("Radiografía")
    col_img.image(result.original_rgb, use_container_width=True)
    col_cam.subheader("Grad-CAM")
    if result.prediction.heatmap is not None:
        col_cam.image(result.prediction.heatmap, use_container_width=True)
    col_res.subheader("Resultado")
    col_res.markdown(f"### :{view.color}[{view.headline}]")
    col_res.metric("Probabilidad", view.probability_text)
    col_res.write(f"**Subtipo sugerido:** {view.subtype_text}")
    col_res.table(
        {"Clase": list(view.probabilities), "Probabilidad": list(view.probabilities.values())}
    )
    if view.metadata_rows:
        with col_res.expander("Metadatos de la imagen"):
            st.table(
                {
                    "Campo": [r[0] for r in view.metadata_rows],
                    "Valor": [r[1] for r in view.metadata_rows],
                }
            )

    patient = st.session_state.get("patient", "anonimo")
    c1, c2 = st.columns(2)
    if c1.button("💾 Guardar en historial", use_container_width=True):
        path = append_history(settings.history_path, patient, result.prediction)
        st.success(f"Guardado en {path.name}.")
    c2.download_button(
        "📄 Descargar reporte PDF",
        data=build_pdf_report(
            result.prediction, result.original_rgb, patient, settings.model_version
        ),
        file_name=f"reporte_{patient}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
