# Especificaciones (spec-driven development)

Cada especificación describe **qué** debe cumplirse con criterios verificables. El agente (o la persona)
convierte cada criterio en una prueba antes de escribir código. Estado: ✅ implementada · 🟡 en curso · ⬜ pendiente.

| Spec | Historia | Estado |
|---|---|---|
| [001 Inferencia por API](001-inferencia-api.md) | HU-01, HU-04 | ✅ |
| [002 Explicabilidad Grad-CAM](002-explicabilidad.md) | HU-02 | ✅ |
| [003 Evaluación con metadatos](003-evaluacion-metadatos.md) | HU-05, HU-06 | 🟡 (falta corrida RSNA 500) |
| [004 Despliegue en Droplet](004-despliegue.md) | HU-07 | 🟡 |
| [005 Hallazgos y vistas 3D](005-hallazgos-3d.md) | HU-08 | ✅ (rama `feature/hallazgos-3d`) |
| [006 Segmentación pulmonar](006-segmentacion-pulmonar.md) | HU-09 | ✅ (rama `feature/segmentacion-pulmonar`) |
| [007 Grad-CAM vs. cajas RSNA](007-localizacion-rsna.md) | HU-10 | 🟡 (código listo; falta la corrida con RSNA) |
| [008 Prototipo de tomografía 3D](008-prototipo-tomografia.md) | HU-11 | 🧪 prototipo (rama `feature/prototipo-tomografia`) |
| [012 Frontend desacoplado](012-frontend-desacoplado/spec.md) (spec + plan + tasks) | HU-13 | ✅ |
| [013 MLflow: 3 runs y Model Registry](013-mlflow-runs-registry/spec.md) (spec + plan + tasks) | HU-14 | ✅ |
| [019 Tablero Kanban en GitHub Projects](019-kanban-github-projects/spec.md) (spec + plan + tasks) | HU: #32 | ✅ |
