"""Tomografía 3D para el frontend desacoplado (SPEC-018).

Expone los casos ya procesados con MEDPSeg (caché `.npz`, ver ADR-0010) para que el cliente HTML/JS
dibuje los pulmones y la lesión en 3D sin Streamlit:

    GET /ct/cases              → {"cases": ["covid_ejemplo", ...]}
    GET /ct/cases/{case_id}    → mallas (vértices y caras en mm, RAS+) + informe por lóbulo
    GET /vendor/plotly.min.js  → Plotly.js del paquete `plotly` instalado (funciona sin internet)

Solo lee la caché: no procesa tomografías nuevas (eso sigue en `make ct-precompute`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from neumonia.config import Settings
from neumonia.controller.ct_analysis import LOBE_LABELS
from neumonia.controller.ct_service import available_cases, load

DECIMALS = 1  # mm: suficiente para la vista y reduce el JSON a la mitad


def plotly_js_path() -> Path:
    import plotly

    return Path(plotly.__file__).resolve().parent / "package_data" / "plotly.min.js"


def case_payload(path: Path) -> dict[str, Any]:
    case, report = load(path)
    structures = {
        name: {
            "vertices": mesh.vertices.round(DECIMALS).tolist(),
            "faces": mesh.faces.astype(int).tolist(),
        }
        for name, mesh in case.meshes.items()
        if len(mesh.faces)
    }
    return {
        "case_id": case.case_id,
        "structures": structures,
        "report": report.to_dict(),
        "lobe_labels": LOBE_LABELS,
    }


def build_ct_router(settings: Settings) -> APIRouter:
    router = APIRouter(tags=["tomografía (prototipo)"])

    @router.get("/ct/cases")
    def list_ct_cases() -> dict[str, list[str]]:
        return {"cases": sorted(available_cases(settings.ct_cache_dir))}

    @router.get("/ct/cases/{case_id}")
    def get_ct_case(case_id: str) -> dict[str, Any]:
        cases = available_cases(settings.ct_cache_dir)
        if case_id not in cases:  # solo nombres de la caché: sin rutas arbitrarias
            raise HTTPException(status_code=404, detail="Caso de tomografía no encontrado.")
        return case_payload(cases[case_id])

    @router.get("/vendor/plotly.min.js", include_in_schema=False)
    def plotly_js() -> FileResponse:
        path = plotly_js_path()
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Plotly.js no está instalado.")
        return FileResponse(path, media_type="application/javascript")

    return router
