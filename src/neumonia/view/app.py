"""Aplicación única: radiografía y tomografía en el mismo puerto (Streamlit multipágina).

Ejecutar: `make ui`  (uv run streamlit run src/neumonia/view/app.py) → http://localhost:8501

Cada página es una de las vistas existentes, sin cambios: `streamlit_app.py` (radiografía, con su
informe) y `ct_app.py` (prototipo de tomografía 3D, con el suyo). No comparten paciente ni informe
todavía: eso es el nivel 2 (informe único por paciente). La página de tomografía solo lee casos
precalculados, así que TensorFlow y PyTorch nunca se cargan en el mismo proceso por su culpa.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

VIEW_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PageSpec:
    script: str
    title: str
    icon: str
    url_path: str
    default: bool = False

    @property
    def path(self) -> Path:
        return VIEW_DIR / self.script


PAGES: tuple[PageSpec, ...] = (
    PageSpec("streamlit_app.py", "Radiografía", "🩻", "radiografia", default=True),
    PageSpec("ct_app.py", "Tomografía 3D (prototipo)", "🫁", "tomografia"),
)


def main() -> None:  # pragma: no cover - lo ejecuta Streamlit
    import streamlit as st

    st.set_page_config(page_title="Apoyo al diagnóstico de neumonía", page_icon="🫁", layout="wide")
    pages = [
        st.Page(
            spec.path,
            title=spec.title,
            icon=spec.icon,
            url_path=spec.url_path,
            default=spec.default,
        )
        for spec in PAGES
    ]
    st.navigation(pages).run()


if __name__ == "__main__":  # Streamlit ejecuta el archivo como __main__
    main()
