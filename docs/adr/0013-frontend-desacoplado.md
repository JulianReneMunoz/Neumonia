# ADR-0013 · Frontend desacoplado HTML/JS en lugar de Streamlit para la demo

- **Estado**: aceptada (13/11/2026)
- **Contexto**: el Anuncio 007 del M3 (cohorte 2026-2S) no califica Streamlit, Gradio ni Dash en la Demo E2E:
  la interfaz debe ser un cliente separado que consuma el backend por HTTP o gRPC. El backend FastAPI ya
  existía con `/health` y `/predict` (spec 001).
- **Decisión**: cliente HTML/CSS/JS propio en `frontend/`, servido con `make frontend` (puerto 5173), que
  llama a la API (`make backend`, puerto 8000) con `fetch`. La API habilita CORS solo para los orígenes de
  `NEUMONIA_CORS_ORIGINS` y carga el modelo una vez al arrancar (lifespan).
- **Consecuencias**: la demo E2E muestra la frontera de servicio (pestaña Network). La app Streamlit
  (`make ui`) se conserva para uso interno y para la página de tomografía (prototipo), pero no se usa en la
  demo del M3. No se agrega Node al proyecto.
- **Alternativas**: React + Vite (más moderno, pero suma Node/pnpm y build); servir el HTML desde FastAPI
  (mismo origen, pero no demuestra el despliegue independiente que pide la rúbrica).
- **Spec**: [SPEC-012](../../specs/012-frontend-desacoplado/spec.md).
