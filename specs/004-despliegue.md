# Spec 004 · Despliegue en Droplet

| # | Criterio de aceptación | Evidencia |
|---|---|---|
| 1 | La imagen CPU construye y el contenedor pasa `scripts/container_smoke.py` | job `docker-build` |
| 2 | Sin CVE críticas con parche | job `trivy` |
| 3 | Despliegue solo desde `main` y con aprobación manual | regla `when: manual` |
| 4 | Credenciales solo como variables protegidas/enmascaradas | `docs/M4_despliegue.md` §2 |
| 5 | Smoke en producción tras desplegar | job `smoke-production` |
| 6 | Reversión a la imagen anterior en < 5 min | `docs/M4_despliegue.md` §6 |
