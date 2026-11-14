# CLAUDE.md — memoria del proyecto Neumonía

Contexto para Claude Code (y cualquier agente de consola). Léelo antes de tocar código.

## Qué es
Apoyo al diagnóstico de neumonía en radiografías de tórax (DICOM/JPG/PNG) con el modelo Keras
`conv_MLP_84.h5` (3 clases: bacteriana, normal, viral) y explicabilidad Grad-CAM.
Proyecto integrador del curso *Gestión de Proyectos en IA y CD* (UAO 2026-2S, caso base).
**El curso no evalúa la exactitud del modelo**: evalúa que se pueda cargar, inferir, probar,
contenerizar y desplegar con un contrato claro.

## Comandos (todo pasa por `uv`; prohibido `pip` y `requirements.txt`)
| Tarea | Comando |
|---|---|
| Entorno | `make install` (= `uv sync --frozen --all-groups`) |
| Modelo | `make model` (descarga + SHA-256) |
| Compuerta completa | `make check` — **córrelo antes de dar una tarea por terminada** |
| Pruebas rápidas | `make test-fast` |
| Smoke del curso | `make smoke` |
| API / UI / gRPC | `make api` · `make ui` · `make grpc` |
| Experimentos | `make evaluate` · `make mlflow` |
| Docker | `make docker-build` · `make docker-up` · `make docker-smoke` |

## Arquitectura (MVC + Estrategia + DIP) — reglas que CI hace cumplir
```
src/neumonia/
  domain.py, config.py         # entidades y configuración (sin dependencias pesadas)
  model/       Modelo          # readers (Estrategia), preprocessing, classifier (DIP), gradcam, metadata
  controller/  Controlador     # service (orquesta), decision (Estrategia), factory (raíz de composición),
                               # gateways (Estrategia local/HTTP), report, errors
  view/        Vista           # streamlit_app (widgets) + presenter (lógica probable)
  api/, grpc_api/              # adaptadores de entrega sobre el controlador
  data/, evaluation.py, tracking/   # CRISP-DM: datos, evaluación, MLflow
```
1. `view/` **nunca** importa `neumonia.model`, TensorFlow ni OpenCV (usa `controller.errors`).
2. `model/` nunca importa controller, view ni api.
3. TensorFlow se importa **dentro de funciones** (arranque y pruebas rápidas).
4. Solo `controller/factory.py` instancia clases concretas (Keras, Grad-CAM).
5. El preprocesamiento (512, gris, CLAHE 2.0/4×4, /255) **no se cambia**: rompe la paridad con el entrenamiento.
`tests/test_architecture.py` falla si se viola 1–3.

## Contrato (no romper)
`POST /predict` → `{label: NORMAL|PNEUMONIA, probability, gradcam_url, ...}`; `422` entrada inválida;
`500 {"error"}`. Campos nuevos solo **aditivos**. Fuente de verdad: `api/openapi.yaml`.

## Convenciones
- Español en código de dominio, docstrings, commits y documentos.
- Pruebas con patrón **AAA** (Arrange/Act/Assert); dobles en `tests/conftest.py`
  (`FakeClassifier`, `FakeExplainer`); marcas `model` y `slow`.
- Cobertura mínima 80 % (compuerta de CI). Ruff, línea de 100.
- Commits: Conventional Commits (`feat(api): ...`, `fix(readers): ...`, `docs: ...`).
- Gitflow: `feature/*` → `develop` → `release/*` → `main` (+ tag `vX.Y.Z`). PR con plantilla.

## Prohibido
- Versionar pesos (`*.h5`), datos (`data/raw`), `.env`, `kaggle.json`, `mlflow.db`.
- Devolver PatientID/PatientName u otra PHI en API, logs o reportes.
- `git push --force` a `main`/`develop`; saltarse `make check`.
- Afirmar exactitud clínica: es una herramienta académica, no un dispositivo médico.

## Skills del proyecto (`.claude/skills/`)
`mvc-feature` · `pytest-aaa` · `api-contract` · `dataset-rsna` · `mlflow-evaluacion` ·
`gradcam-review` · `gitflow-pr` · `docker-deploy` · `entregables-curso` · `graphify`.
Subagentes (`.claude/agents/`): `revisor-arquitectura`, `escritor-pruebas`.

## Arquitectura documentada
`docs/arquitectura/DESIGN.md` (diseño técnico, 12 diagramas C4/4+1 en `docs/arquitectura/diagramas/`) y
`docs/arquitectura/METODOLOGIAS_ARQUITECTURA.md` (cada metodología ↔ componente ↔ evidencia). Si cambias la
arquitectura, actualiza el `.mmd` correspondiente y ejecuta `make diagramas`.

## graphify — mapa del código (`graphify-out/`)
- Si existe `graphify-out/graph.json`, usa `uv run graphify query "<pregunta>"` **antes** del primer grep o lectura
  de archivos para una pregunta sobre el código; `uv run graphify explain "<concepto>"` y
  `uv run graphify path "<A>" "<B>"` para relaciones. Incluye esta regla en el prompt de cada subagente que explore código.
- Para navegación amplia usa `graphify-out/wiki/index.md`; lee `graphify-out/GRAPH_REPORT.md` solo para revisiones de arquitectura.
- Después de modificar código ejecuta `make grafo` (AST, sin LLM ni costo). Un diff grande en `graph.json` es esperado.

## Engram — memoria de decisiones (proyecto `neumonia`)
- Al iniciar: recupera contexto con `mem_context` / `mem_search` (MCP) o `engram search "<tema>" --project neumonia`.
- Antes de proponer cambiar una decisión (umbral, preprocesamiento, dataset, contrato), **búscala**: no re-litigues ADR.
- Guarda con `mem_save` solo decisiones, hallazgos o convenciones nuevas, con `topic_key` estable
  (`decision/*`, `architecture/*`, `discovery/*`). Las memorias del equipo se versionan en `scripts/engram_memoria.py`.
- Antes de terminar la sesión: `mem_session_summary`.
