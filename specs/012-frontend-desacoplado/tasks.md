# Tareas · SPEC-012

- [x] T1. `config.py`: `cors_origins` + `NEUMONIA_CORS_ORIGINS` (AC3).
- [x] T2. `api/app.py`: `CORSMiddleware` con `expose_headers=["X-Process-Time-ms"]` (AC1, AC2).
- [x] T3. `api/app.py`: `lifespan` + `warm_up()` que carga el modelo una vez y tolera su ausencia (AC4, AC5).
- [x] T4. `frontend/index.html` con los 4 estados y el panel del paciente.
- [x] T5. `frontend/app.js`: health, predict con timeout, errores 422/500/red, render con `textContent` (AC6).
- [x] T6. `frontend/styles.css` y `config.js`.
- [x] T7. `Makefile`: `make backend` y `make frontend`.
- [x] T8. `tests/test_frontend_desacoplado.py` (AC1–AC6).
- [x] T9. E2E con Playwright: DICOM, JPG y archivo inválido (AC7, AC8).
- [x] T10. README, CHANGELOG, ADR-0013 y specs/README.md.
