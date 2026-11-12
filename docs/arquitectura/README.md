# Arquitectura — índice

| Documento | Contenido |
|---|---|
| [DESIGN.md](DESIGN.md) | Documento de diseño técnico: impulsores, atributos de calidad, 12 vistas (C4 + 4+1), ADR, interfaces, riesgos |
| [METODOLOGIAS_ARQUITECTURA.md](METODOLOGIAS_ARQUITECTURA.md) | Matriz y explicación: cada una de las 23 metodologías ↔ elemento de arquitectura, diagrama, evidencia, graphify y Engram |
| [GRAFO_GRAPHIFY.md](GRAFO_GRAPHIFY.md) | Grafo de conocimiento del repositorio y lo que revela de la arquitectura |
| [MEMORIA_ENGRAM.md](MEMORIA_ENGRAM.md) | Memoria persistente de decisiones para los agentes |
| [diagramas/](diagramas/) | 12 diagramas Mermaid (`.mmd`, editables) exportados a `.svg` |

## Diagramas
| # | Diagrama | Vista |
|---|---|---|
| 01 | [Contexto](diagramas/01-contexto.svg) | C4 nivel 1 |
| 02 | [Contenedores](diagramas/02-contenedores.svg) | C4 nivel 2 |
| 03 | [Componentes MVC](diagramas/03-componentes-mvc.svg) | C4 nivel 3 |
| 04 | [Clases y protocolos](diagramas/04-clases.svg) | C4 nivel 4 / lógica |
| 05 | [Secuencia POST /predict](diagramas/05-secuencia-predict.svg) | Procesos |
| 06 | [Secuencia de evaluación](diagramas/06-secuencia-evaluacion.svg) | Procesos |
| 07 | [Despliegue](diagramas/07-despliegue.svg) | Física |
| 08 | [Pipeline CI/CD](diagramas/08-pipeline-cicd.svg) | Desarrollo |
| 09 | [CRISP-DM y datos](diagramas/09-crisp-dm-datos.svg) | Escenarios |
| 10 | [Metodologías → arquitectura](diagramas/10-metodologias-arquitectura.svg) | Trazabilidad |
| 11 | [Flujo agéntico](diagramas/11-flujo-agentico.svg) | Desarrollo |
| 12 | [Dependencias medidas con graphify](diagramas/12-dependencias-graphify.svg) | Verificación |

Editar: modifica el `.mmd` y ejecuta `make diagramas`. GitHub, GitLab y VS Code (extensión *Markdown Preview Mermaid*)
también renderizan Mermaid directamente.
