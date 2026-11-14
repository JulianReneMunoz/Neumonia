# Plan · SPEC-018

- **API** (`src/neumonia/api/ct_routes.py`): `build_ct_router(settings)` reutiliza
  `controller.ct_service.available_cases/load`; redondea vértices a 0,1 mm (≈2,9 MB para
  `covid_ejemplo`); omite mallas vacías; se registra en `api/app.py` con `include_router`.
- **Frontend** (`frontend/app.js`, `index.html`, `styles.css`): selector segmentado dentro de la
  pestaña 3D; carga perezosa de Plotly.js desde la API; trazas `mesh3d` con la paleta `CT_STYLE`
  replicada de `view/ct_views.py`; la leyenda de Plotly permite ocultar estructuras.
- **Caché del navegador**: `?v=18` en `styles.css`, `config.js` y `app.js`.
- **Riesgos**: si la API es antigua, el visor muestra «reinicie make backend»; si la caché está vacía,
  indica ejecutar `make ct-precompute`.
