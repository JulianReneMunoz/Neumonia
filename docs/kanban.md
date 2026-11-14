# Tablero Kanban del proyecto

> Copia versionada del tablero **[Neumonía · Kanban](https://github.com/users/JulianReneMunoz/projects/5)** (GitHub Projects #5).
> Fecha de corte: **2026-11-14** · Se regenera con `make kanban` (SPEC-019).

## Política Kanban

| Columna | Definición |
|---|---|
| **Backlog** | Ideas e historias registradas que aún no se priorizan para el módulo en curso. |
| **Todo** | Historias priorizadas, con criterios de aceptación, listas para empezar. |
| **In Progress** | Trabajo en desarrollo en una rama `feature/*` o `fix/*`. Límite WIP: **3**. |
| **En revisión** | PR abierto hacia `develop`, a la espera de CI en verde y revisión. |
| **Done** | PR fusionado con CI en verde (lint, pruebas en Ubuntu y Windows, Docker) o issue cerrado. |

- **Límite WIP:** como máximo 3 ítems en *In Progress*; si se alcanza, se termina o se revisa antes de empezar algo nuevo.
- **Criterio de Done:** PR fusionado en `develop` con CI en verde; el issue asociado se cierra con `Closes #n`.
- **Flujo:** una historia (issue) por funcionalidad → rama `feature/*` → PR a `develop` → Done.

## Conteo por columna

| Columna | Ítems |
|---|:-:|
| Backlog | 0 |
| Todo | 1 |
| In Progress | 0 |
| En revisión | 1 |
| Done | 30 |
| **Total** | **32** |

## Backlog

_Sin ítems._

## Todo

| # | Título | Tipo | Etiquetas | Enlace |
|:-:|---|:-:|---|---|
| 32 | HU: Tablero Kanban del proyecto en GitHub Projects | Issue | `docs` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/32) |

## In Progress

_Sin ítems._

## En revisión

| # | Título | Tipo | Etiquetas | Enlace |
|:-:|---|:-:|---|---|
| 31 | docs(readme): README visual del M3 | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/31) |

## Done

| # | Título | Tipo | Etiquetas | Enlace |
|:-:|---|:-:|---|---|
| 30 | feat(mlflow): 3 corridas comparables y Model Registry en el puerto 5050 (SPEC-013) | PR | `docs` `mlflow` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/30) |
| 29 | HU: Comparar 3 configuraciones en MLflow y registrar el modelo servido | Issue | `docs` `mlflow` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/29) |
| 28 | feat(frontend): informe detallado y tomografía 3D con pulmones y lesión (SPEC-017, SPEC-018) | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/28) |
| 27 | feat(frontend): cliente HTML/JS desacoplado de la API REST (SPEC-012, ADR-0013) | PR | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/27) |
| 26 | HU: Usar el sistema desde un navegador que llama a la API | Issue | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/26) |
| 25 | feat(ui): datos y código del paciente en la barra lateral (seudónimo y código del dataset) | PR | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/25) |
| 24 | HU: Datos y código seudónimo del paciente en la barra lateral | Issue | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/24) |
| 23 | feat(ui): punto de entrada de la app única (app.py) y su prueba | PR | `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/23) |
| 22 | HU: Una sola aplicación para radiografía y tomografía | Issue | `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/22) |
| 21 | docs(readme): modelos preentrenados, flujo del sistema y ficha técnica | PR | `docs` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/21) |
| 20 | HU: Explicar en el README qué modelos usa el sistema y cómo se integran | Issue | `docs` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/20) |
| 19 | docs(model-card): resultados en RSNA de localización y clasificación por subgrupo | PR | `docs` `mlflow` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/19) |
| 18 | HU: Resultados medidos en RSNA en la Model Card | Issue | `docs` `mlflow` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/18) |
| 17 | feat(tomografia): prototipo de reconstrucción 3D de tomografía con MEDPSeg (HU-11) | PR | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/17) |
| 16 | HU: Ver en 3D la lesión de una tomografía (prototipo) | Issue | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/16) |
| 15 | feat(evaluacion): localización de Grad-CAM frente a las cajas de RSNA (HU-10) | PR | `backend` `docs` `mlflow` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/15) |
| 14 | HU: Medir si Grad-CAM apunta a la lesión marcada por radiólogos | Issue | `backend` `docs` `mlflow` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/14) |
| 13 | feat(segmentacion): segmentación pulmonar real con PSPNet (HU-09) | PR | `backend` `docs` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/13) |
| 12 | HU: Zonas del informe con la forma real de los pulmones | Issue | `backend` `docs` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/12) |
| 11 | fix(ci): liberar disco antes de construir la imagen CPU (SPEC-015) | PR | `backend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/11) |
| 10 | HU: Que el CI no se quede sin disco al construir la imagen Docker | Issue | `backend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/10) |
| 9 | feat(hallazgos): informe de hallazgos por zonas pulmonares y vistas 3D (HU-08) | PR | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/9) |
| 8 | HU: Informe de hallazgos por zonas del pulmón y vista 3D | Issue | `backend` `docs` `frontend` `qa` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/8) |
| 7 | docs: nombre «apoyo al diagnóstico de neumonía» en vez de «detector» | PR | `docs` `frontend` | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/7) |
| 6 | HU: Llamar al sistema «apoyo al diagnóstico» y no «detector» | Issue | `docs` `frontend` | [abrir](https://github.com/JulianReneMunoz/Neumonia/issues/6) |
| 5 | docs: captura real de la UI Streamlit | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/5) |
| 4 | docs: captura real de la UI Streamlit | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/4) |
| 3 | docs: autoría de esta versión y créditos de componentes de terceros | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/3) |
| 2 | release: v0.3.0 - M3 construcción local | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/2) |
| 1 | fix(ci): UTF-8 en runner Windows | PR | — | [abrir](https://github.com/JulianReneMunoz/Neumonia/pull/1) |
