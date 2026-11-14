# SPEC-015 · CI: liberar disco antes de construir la imagen CPU

**Historia**: Como equipo, quiero que el job `docker` del CI libere espacio en el runner antes de construir
la imagen CPU, para que la compuerta de Docker no falle por falta de disco y no bloquee las fusiones.

## Problema
El runner gratuito `ubuntu-latest` de GitHub Actions trae preinstaladas herramientas que el proyecto no usa
(.NET, Android SDK, GHC, CodeQL). Al construir la imagen CPU (TensorFlow + extras), el job `docker` se queda
sin disco: en la PR #9 falló dos veces con `System.IO.IOException: No space left on device` durante el paso
«Build imagen CPU», con lint y pruebas en verde.

## Requisitos
- RF1. El job `docker` de `.github/workflows/ci.yml` tiene un paso «Liberar espacio en disco» **antes** del
  paso «Build imagen CPU».
- RF2. El paso borra `/usr/share/dotnet`, `/usr/local/lib/android`, `/opt/ghc` y
  `/opt/hostedtoolcache/CodeQL`, y ejecuta `docker system prune -af`.
- RF3. El paso muestra el espacio libre antes y después (`df -h /`), para que el log deje evidencia.
- RNF. No cambia la imagen, el Dockerfile ni los demás jobs; no agrega acciones de terceros.

## Criterios de aceptación (Given-When-Then)
| # | Criterio | Prueba |
|---|---|---|
| 1 | Dado el workflow de CI, cuando se lee el job `docker`, entonces el paso que libera espacio está antes del build y borra las 4 rutas y hace `docker system prune -af` | `tests/test_ci_workflow.py::test_docker_job_frees_disk_before_building_the_image` |
| 2 | Dado el paso de limpieza, cuando corre en el runner, entonces el log muestra `df -h /` antes y después | Log del job `docker` en la PR del fix |
| 3 | Dado el CI corregido en `develop`, cuando se vuelve a ejecutar la PR #9 (cerrar y reabrir), entonces el job `docker` pasa | Checks de la PR #9 |

## Fuera de alcance
Reducir el tamaño de la imagen (multi-stage, TensorFlow CPU más liviano); runners propios o de pago.

## Métrica de éxito
El job `docker` pasa en la PR #9 y en las siguientes PRs de la serie del M3 sin reintentos.
