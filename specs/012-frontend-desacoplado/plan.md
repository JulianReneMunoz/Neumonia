# Plan · SPEC-012 Frontend desacoplado

## Diseño
```
Navegador (frontend/, :5173) ──fetch HTTP/JSON──▶ FastAPI (api/app.py, :8000)
                                                   └─▶ PneumoniaService (controller) ─▶ KerasClassifier + Grad-CAM (model)
```
- **Cliente**: `index.html` (estructura y estados), `app.js` (fetch, estados, render), `styles.css`,
  `config.js` (URL de la API y timeout, editables sin tocar el código).
- **Contrato**: el de siempre, `api/openapi.yaml`. El cliente no conoce el modelo: solo JSON.
- **Servido**: `python -m http.server` vía `uv run` (sin Node), en otro puerto → otro origen → CORS.

## Decisiones
| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| HTML/JS propio sin framework | El anuncio lo acepta; cero dependencias nuevas y sin paso de build en la máquina de la demo | React/Vite: requiere Node/pnpm y más tiempo de instalación |
| CORS con lista explícita de orígenes | Mínimo privilegio; `*` permitiría a cualquier página usar la API | `allow_origins=["*"]` |
| Precarga del modelo en `lifespan` | Lo pide la rúbrica (carga una vez al arrancar) y quita la latencia de la 1.ª petición | Carga perezosa en la primera petición (comportamiento anterior) |
| Arrancar aunque falte el modelo | `/health` debe poder decir «modelo sin cargar» en vez de que el proceso muera | Fallar en el arranque |
| `textContent` para metadatos | Los DICOM traen texto arbitrario: evita inyección de HTML | `innerHTML` |

Ver ADR-0013.

## Riesgos
- Puerto 5173 ocupado → cambiar en `make frontend` y en `NEUMONIA_CORS_ORIGINS`.
- El navegador no muestra DICOM: se explica en la UI y se muestra el Grad-CAM sobre la imagen procesada.

## Estrategia de pruebas
- pytest (sin red ni GPU): CORS, lifespan, arranque sin modelo y contrato estático del cliente.
- E2E con Playwright (fuera de CI): DICOM → éxito con panel del paciente; JPG → vista previa; texto → 422.
