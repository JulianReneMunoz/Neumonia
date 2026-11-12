# Grafo de conocimiento del proyecto (graphify)

[graphify](https://github.com/safishamsi/graphify) convierte el repositorio (código, YAML, Markdown) en un grafo
consultable. Claude Code lo usa como **mapa** antes de leer archivos, lo que reduce el contexto y los errores.

## Salidas (`graphify-out/`)
| Archivo | Uso |
|---|---|
| `graph.html` | Grafo interactivo. Ábrelo en el navegador (necesita internet para la librería de visualización) |
| `graph.svg` | Imagen estática del grafo completo ([vista previa](../img/graphify_grafo.png)) |
| `Neumonia-callflow.html` | Diagramas de flujo de llamadas en Mermaid, generados del código |
| `GRAPH_REPORT.md` | Nodos centrales (*god nodes*), comunidades, conexiones sorprendentes y preguntas sugeridas |
| `graph.json` | Grafo completo; lo consultan `graphify query/explain/path` |
| `wiki/` | Un artículo por comunidad; `wiki/index.md` es la entrada para agentes |

## Comandos
```powershell
make grafo                                   # = uv run graphify update .   (AST, sin LLM, sin costo)
uv run graphify explain "PneumoniaService"   # vecinos de un concepto
uv run graphify path "streamlit_app.py" "KerasClassifier"
uv run graphify query "¿dónde se valida la entrada?"
```
Dentro de Claude Code: `/graphify .` hace la extracción completa, incluida la semántica de los documentos con el LLM.

## Resultados (12/11/2026)
- **1 025 nodos · 1 926 aristas · 81 comunidades · 0 ciclos de importación.**
- 89 % de las aristas son extraídas del AST y 11 % inferidas (confianza media 0.93).

**Nodos centrales y su lectura arquitectónica**
| # | Nodo | Aristas | Lectura |
|---|---|---|---|
| 1 | `PneumoniaService` | 43 | El controlador es el núcleo, como exige MVC |
| 2 | `InvalidImageError` | 26 | La validación en la frontera atraviesa API, gRPC, UI y evaluación |
| 3 | `evaluate()` | 26 | Puente entre datos, servicio y tracking (CRISP-DM fase 5) |
| 4–8 | `FakeClassifier`, `Settings`, `Prediction`, `FakeExplainer`, `create_app()` | 20–22 | Testabilidad por DIP, configuración 12-factor y contrato único |
| 9 | `ThresholdPolicy` | 19 | La regla de negocio (análisis de decisión), enlazada desde `metodologias.md` y `DESIGN.md` |

**Dependencias entre capas**: ver el diagrama [12](diagramas/12-dependencias-graphify.svg). Vista→Modelo y
Modelo→Controlador son **0**: el grafo confirma de forma independiente la regla que prueba `test_architecture.py`.

**Conexiones documento ↔ código** (ejemplos reales de `GRAPH_REPORT.md`):
- `metodologias.md §7 MVC` → `PneumoniaService`
- `metodologias.md §17 Análisis de decisión` → `ThresholdPolicy`
- `skill mvc-feature` → `Classifier`, `read_image()`
- `skill pytest-aaa` → `InvalidImageError`
- `DESIGN.md §3.5 POST /predict` → `ThresholdPolicy`
- `DESIGN.md §3.2 Contenedores` → `HttpGateway`

## Integración con Claude Code
- Skill del proyecto: `.claude/skills/graphify/` (versión 0.9.107).
- Hooks en `.claude/settings.json`: antes de cada `Grep`/`Glob`/`Read`, `graphify hook-guard` recuerda consultar el
  grafo. Tras una compactación, `SessionStart` reinicia el recordatorio.
- `CLAUDE.md`, sección *graphify*: reglas de uso.
- `.graphifyignore` excluye datos, pesos, imágenes, `.venv` y código generado.

> Regenera el grafo después de cambiar código (`make grafo`). Un *diff* grande en `graph.json` dentro de un PR es esperado.
