---
name: docker-deploy
description: Construye, ejecuta, prueba y despliega los contenedores CPU del proyecto Neumonía (Docker Compose local y Droplet vía GitLab CI/CD). Úsala para el M1 (Docker CPU) y el M4 (producción), o para diagnosticar fallas del contenedor.
---

# Docker y despliegue

## Local
```bash
make docker-build          # docker compose build (imagen CPU multi-etapa, usuario no root)
make docker-up             # api :8000 · ui :8501 (UI → API por HttpGateway)
make docker-smoke          # /health, POST /predict, gradcam_url y 422
docker compose --profile mlops up -d   # + MLflow :5000
docker compose logs -f api
```

## Imagen (`docker/Dockerfile`)
- Base `python:3.13-slim-bookworm`, `uv sync --frozen --no-dev` (sin pip).
- El modelo se descarga en el build y se verifica con SHA-256 (no viaja en el contexto).
- `HEALTHCHECK` en `/health`, `EXPOSE 8000`, `CUDA_VISIBLE_DEVICES=""` (solo CPU).
- La UI usa la misma imagen con otro `command`.

## Producción (M4) — Droplet DigitalOcean
1. Droplet Ubuntu 24.04, 2 vCPU / 4 GB (TensorFlow CPU necesita ~1.5 GB).
2. En el Droplet: instalar Docker, crear usuario `deploy` en el grupo `docker`, `mkdir ~/neumonia`.
3. GitLab → Settings → CI/CD → Variables (Protected + Masked):
   `DROPLET_HOST`, `DROPLET_USER`, `SSH_PRIVATE_KEY` (tipo File), `SSH_KNOWN_HOSTS` (`ssh-keyscan <ip>`).
4. Merge a `main` → pipeline: ruff → pytest (≥80 %) → build + smoke → Trivy → **deploy manual** → smoke en producción.
5. Firewall: abrir 8501 (UI); 8000 solo si la API es pública.

## Diagnóstico
| Síntoma | Causa probable |
|---|---|
| `ModelNotFoundError` | Falló `fetch_model.py` en el build (red o SHA). Ver logs del build. |
| Contenedor `unhealthy` | Arranque lento de TF: aumentar `start-period`. |
| `Killed` / OOM | Memoria < 2 GB: subir el Droplet o limitar workers. |
| UI "No fue posible consultar la API" | `NEUMONIA_API_URL` mal o `api` aún no saludable. |
