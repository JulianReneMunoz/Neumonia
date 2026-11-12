# Spec 001 · Inferencia por API

**Objetivo**: clasificar radiografías por `POST /predict` cumpliendo `api/openapi.yaml`.

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | DICOM, JPG y PNG válidos → 200 con `label`, `probability`, `gradcam_url` | `test_api.py::test_predict_ok_with_course_samples` |
| 2 | El formato se detecta por firma binaria antes que por extensión | `test_readers.py::test_select_reader_prefers_signature_over_extension` |
| 3 | Vacío, texto, PNG/DICOM corrupto o sin extensión → 422 con `detail` | `test_api.py::test_predict_invalid_returns_422` |
| 4 | > `NEUMONIA_MAX_UPLOAD_MB` → 422 | `test_api.py::test_predict_too_large_returns_422` |
| 5 | Excepción del modelo → 500 `{"error": ...}` sin traza | `test_api.py::test_model_failure_returns_500_with_error` |
| 6 | La respuesta nunca contiene rutas locales ni PatientID | `test_api.py::test_response_has_no_local_paths` |
| 7 | `GET /health` → 200 `{status: ok, ...}` | `test_api.py::test_health` |
