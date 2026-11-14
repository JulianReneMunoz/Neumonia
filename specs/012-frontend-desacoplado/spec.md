# SPEC-012 · Frontend desacoplado (cliente HTML/JS de la API REST)

**Historia**: Como médico, quiero usar el sistema desde un navegador que llame a la API, para que la
interfaz y el modelo vivan en procesos separados y el backend sirva a cualquier cliente.

## Problema
La interfaz del M3 era Streamlit: la UI y la inferencia corrían en el mismo proceso. El Anuncio 007
(M3, cohorte 2026-2S) no califica Streamlit en la Demo E2E: exige un cliente separado que consuma el
backend por HTTP, con estados visibles y la llamada en la pestaña Network.

## Requisitos
- RF1. Cliente HTML/CSS/JS propio en `frontend/`, servido aparte (`make frontend`, puerto 5173).
- RF2. Consume `GET /health` y `POST /predict` de la API (`make backend`, puerto 8000) con `fetch`.
- RF3. Estados `idle`, `loading`, `success` y `error`, con reintento.
- RF4. Muestra etiqueta, confianza, subtipo, probabilidades por clase, Grad-CAM y datos del paciente
  (mismas filas que `presenter.patient_rows`; nunca PatientName).
- RF5. La API permite CORS solo a los orígenes de `NEUMONIA_CORS_ORIGINS` y expone `X-Process-Time-ms`.
- RF6. El modelo se carga una vez al arrancar la API (lifespan); sin modelo, `/health` → `model_loaded: false`.
- RNF. Sin dependencias de Node ni paso de compilación; los metadatos se pintan con `textContent`.

## Criterios de aceptación (Given-When-Then)
| # | Criterio | Prueba |
|---|---|---|
| 1 | Dado el frontend en :5173, cuando hace una petición a la API, entonces la respuesta trae `access-control-allow-origin` de ese origen | `test_frontend_desacoplado.py::test_cors_allows_the_frontend_origin_and_exposes_latency` |
| 2 | Dado un origen no listado, cuando llama a la API, entonces no recibe cabecera CORS | `::test_cors_rejects_unknown_origins` |
| 3 | Dado `NEUMONIA_CORS_ORIGINS`, cuando arranca la API, entonces usa esos orígenes | `::test_cors_origins_come_from_the_environment` |
| 4 | Dada la API arrancando, cuando aún no llega ninguna petición, entonces el servicio ya está construido una sola vez | `::test_model_is_loaded_once_at_startup` |
| 5 | Dado que falta el `.h5`, cuando arranca la API, entonces responde `/health` con `model_loaded: false` | `::test_api_starts_even_if_the_model_is_missing` |
| 6 | Dado el cliente, entonces usa `fetch` a `/predict` y `/health`, declara los 4 estados y no usa Streamlit ni `innerHTML` | `::test_frontend_is_a_separate_client_of_the_api` |
| 7 | Dada una radiografía DICOM en el navegador, cuando pulsa Predecir, entonces ve loading → resultado con Grad-CAM y el panel del paciente | E2E manual / Playwright (plan.md) |
| 8 | Dado un archivo que no es imagen, cuando pulsa Predecir, entonces ve el estado error con el mensaje 422 y el botón Reintentar | E2E manual / Playwright |

## Fuera de alcance
La página de tomografía 3D (sigue siendo prototipo); autenticación; despliegue del frontend en el Droplet (M4).

## Métrica de éxito
Demo E2E sin Streamlit: la petición `POST /predict` visible en Network y respuesta en < 2 s en CPU.
