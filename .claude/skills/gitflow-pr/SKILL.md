---
name: gitflow-pr
description: Gestiona ramas, commits y pull/merge requests del proyecto Neumonía con Gitflow y Conventional Commits. Úsala al iniciar una tarea, preparar un PR o liberar una versión.
---

# Gitflow + Conventional Commits

## Ramas
| Rama | Desde | Hacia | Uso |
|---|---|---|---|
| `main` | — | — | Producción. Solo merges de `release/*` y `hotfix/*`. Tag `vX.Y.Z`. |
| `develop` | `main` | — | Integración continua. |
| `feature/HU-0X-descripcion` | `develop` | `develop` | Una historia de usuario por rama. |
| `release/vX.Y.Z` | `develop` | `main` + `develop` | Congelar, ajustar versión y CHANGELOG. |
| `hotfix/descripcion` | `main` | `main` + `develop` | Corrección urgente. |

## Iniciar una tarea
```bash
git switch develop && git pull
git switch -c feature/HU-03-reporte-pdf
```

## Commits
`<tipo>(<ámbito>): <resumen en imperativo>` — tipos: `feat, fix, test, docs, refactor, ci, build, chore`.
Ejemplos: `feat(api): agrega request_id a /predict` · `fix(readers): invierte MONOCHROME1`.

## Antes del PR
1. `make check` en verde.
2. `git diff develop --stat` sin `*.h5`, `data/`, `.env`.
3. Completa `.github/pull_request_template.md` (GitLab: `.gitlab/merge_request_templates/Default.md`).
4. Un revisor humano distinto del autor aprueba. El agente **no** hace merge.

## Liberar
```bash
git switch -c release/v0.3.0 develop
# actualizar version en pyproject.toml y src/neumonia/__init__.py; uv lock
git commit -am "build: v0.3.0"
# PR release → main; tras el merge:
git tag -a v0.3.0 -m "M3: construcción local" && git push origin v0.3.0
```
Versionado semántico: MAJOR rompe el contrato, MINOR agrega funcionalidad, PATCH corrige.
