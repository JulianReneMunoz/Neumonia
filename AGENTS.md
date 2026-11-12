# AGENTS.md

Instrucciones para agentes de código en consola (Claude Code, OpenCode, Antigravity CLI, Cursor Agent).
La fuente completa es [`CLAUDE.md`](CLAUDE.md); este archivo resume lo indispensable para
agentes que no leen `CLAUDE.md`.

## Antes de editar
1. `make install` y `make model`.
2. Lee `CLAUDE.md` (arquitectura y reglas) y la historia de usuario en `docs/M2_propuesta.md`.
3. Si la tarea tiene especificación en `specs/`, trabaja contra sus criterios de aceptación.
4. Consulta el mapa del código con `uv run graphify query "<pregunta>"` (grafo en `graphify-out/`) y la memoria de
   decisiones con `engram search "<tema>" --project neumonia` antes de leer archivos o proponer cambios.
5. Arquitectura y trazabilidad de metodologías: `docs/arquitectura/`.

## Bucle de trabajo (spec → prueba → código → compuerta)
1. Escribe o actualiza la prueba (AAA) que expresa el criterio de aceptación.
2. Implementa en la capa correcta (Modelo / Controlador / Vista / adaptador).
3. `make check` debe pasar (ruff + formato + pytest con cobertura ≥ 80 %).
4. Resume el cambio para el PR usando `.github/pull_request_template.md`.

## Límites
- No modifiques el preprocesamiento ni el contrato `label/probability/gradcam_url`.
- No agregues dependencias con `pip`: usa `uv add <paquete>` y versiona `uv.lock`.
- No subas pesos, datos ni secretos. No expongas datos del paciente.
- Un humano revisa y aprueba cada PR (ver `docs/declaracion_uso_ia.md`).
