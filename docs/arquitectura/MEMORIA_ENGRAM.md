# Memoria persistente del proyecto (Engram)

[Engram](https://github.com/Gentleman-Programming/engram) (Gentleman Programming) da **memoria entre sesiones** a los
agentes de código. Es un binario único en Go, con SQLite + FTS5 y un servidor MCP. graphify responde *cómo está hecho*
el código; Engram responde **por qué** se decidió así y **qué se descubrió**.

## Qué hay en el repositorio
| Ruta | Contenido |
|---|---|
| `.engram/config.json` | `{"project_name": "neumonia"}`, que fija el proyecto para el CLI y el MCP |
| `.engram/manifest.json` + `.engram/chunks/*.jsonl.gz` | 18 memorias exportadas (Git Sync, sin *prompts*) |
| `scripts/engram_memoria.py` | **Fuente versionada** de las memorias. Se revisa por PR, como el código |

## Las 18 memorias
| Tipo | Topic | Título |
|---|---|---|
| architecture | `architecture/mvc-estrategia-dip` | Arquitectura MVC + Estrategia + DIP |
| architecture | `architecture/contrato-api` | Contrato estable de POST /predict |
| decision | `decision/modelo-preentrenado` | Se reutiliza conv_MLP_84.h5 |
| decision | `decision/politica-umbral` | Política 3 clases → contrato binario |
| decision | `decision/dataset-rsna` | Dataset con metadatos: RSNA 2018 |
| decision | `decision/ui-gateway` | UI Streamlit con pasarela Local/HTTP |
| decision | `decision/mlflow-sqlite` | MLflow con backend SQLite |
| decision | `decision/privacidad` | Privacidad: nunca exponer PHI |
| decision | `decision/metodologias` | Metodologías del proyecto |
| pattern | `pattern/pruebas-aaa` | Pruebas pytest AAA con dobles |
| config | `config/preprocesamiento` | NO cambiar el preprocesamiento |
| config | `config/comandos` | Comandos del proyecto |
| config | `config/ci-cd` | CI/CD con compuertas |
| config | `config/entregables` | Entregables y fechas del curso |
| config | `config/herramientas-agente` | Herramientas agénticas del proyecto |
| discovery | `discovery/gradcam-atajos` | Grad-CAM revela posible aprendizaje por atajos |
| discovery | `discovery/falso-positivo` | Falso positivo con alta confianza |
| learning | `learning/metricas-aula` | Métricas del aula están infladas |

## Uso en Windows (`C:\Neumonia`) con Engram en WSL
En este equipo, Claude Code arranca Engram **dentro de WSL (Ubuntu)**:
`claude mcp get engram` → `wsl.exe -d Ubuntu -e /home/linuxbrew/.linuxbrew/bin/engram mcp`.
Por eso los objetivos del Makefile llaman al binario de WSL, para que la memoria del proyecto viva en la **misma
base** que usa el agente y que comparten tus otros proyectos.
```powershell
cd C:\Neumonia
make memoria                          # importa .engram/chunks al Engram de WSL (18 memorias)
make memoria-buscar Q="umbral"        # buscar
make memoria-exportar                 # tras editar scripts/engram_memoria.py: guarda y exporta a .engram/
```
Otra distro o ruta: `make memoria ENGRAM_DISTRO=Ubuntu-24.04 ENGRAM_BIN=/usr/local/bin/engram`.

> No ejecutes `engram setup claude-code` desde el Engram de Windows. Instalaría hooks que escriben en otra base
> (`C:\Users\<usuario>\.engram`) y la memoria quedaría dividida. Si algún día migras todo a Windows: exporta desde WSL
> (`engram export`), importa en Windows y solo entonces cambia el registro MCP.
Al agregar o cambiar una decisión, edita `scripts/engram_memoria.py` y ejecuta `make memoria-exportar`.
El `topic` es estable, así que se actualiza en vez de duplicarse. Luego versiona `.engram/` en el PR.

## Protocolo de memoria para el agente
Según la documentación de Engram:
1. Al iniciar, confirma el proyecto y recupera el contexto (`mem_context`, `mem_search`).
2. Busca antes de revisar una decisión conocida, para no re-litigar ADR.
3. Guarda con `mem_save` solo conocimiento significativo (decisión, arquitectura, hallazgo), no salidas crudas.
4. Usa `topic_key` estables para temas que evolucionan.
5. Antes de cerrar, guarda `mem_session_summary` como traspaso.

> `.engram/` puede contener información sensible: revísalo antes de compartir. Las memorias de este proyecto no tienen
> datos de pacientes.
