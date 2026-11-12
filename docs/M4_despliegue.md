# M4 · Producción: CI/CD, despliegue, monitoreo y demo

## 1. Pipeline (`.gitlab-ci.yml`)
```
lint ─► test ─► build ─► scan ─► deploy (manual) ─► verify
ruff    pytest   docker   Trivy   Droplet            smoke en producción
        ≥80 %    + smoke  CVE
        + smoke  + push
```
| Compuerta | Falla si… |
|---|---|
| `ruff` | hay errores de estilo o formato |
| `pytest` | falla una prueba o la cobertura < 80 % o falla `smoke_infer.py` |
| `docker-build` | la imagen no construye o el contenedor no responde `/health`, `/predict` y 422 |
| `trivy` | la imagen tiene CVE **críticas** con parche disponible |
| `deploy-droplet` | requiere aprobación humana (supervisión) y solo corre en `main` |
| `smoke-production` | el servicio publicado no cumple el contrato |

## 2. Credenciales (nunca en el repositorio)
GitLab → Settings → CI/CD → Variables, todas **Protected** y **Masked**:

| Variable | Tipo | Contenido |
|---|---|---|
| `DROPLET_HOST` | Variable | IP pública del Droplet |
| `DROPLET_USER` | Variable | `deploy` |
| `SSH_PRIVATE_KEY` | **File** | llave ed25519 solo para despliegue |
| `SSH_KNOWN_HOSTS` | Variable | salida de `ssh-keyscan <ip>` (evita ataques MITM) |
`CI_REGISTRY_*` las inyecta GitLab. Localmente, `.env` (copiado de `.env.example`) está en `.gitignore`.

## 3. Preparar el Droplet (una vez)
```bash
# Ubuntu 24.04, 2 vCPU / 4 GB, región NYC/SFO
adduser --disabled-password deploy && usermod -aG docker deploy
curl -fsSL https://get.docker.com | sh
mkdir -p /home/deploy/neumonia && chown deploy: /home/deploy/neumonia
ufw allow OpenSSH && ufw allow 8501 && ufw allow 8000 && ufw enable
# en ~deploy/.ssh/authorized_keys: la llave pública correspondiente a SSH_PRIVATE_KEY
```

## 4. Monitoreo
| Señal | Cómo | Umbral / acción |
|---|---|---|
| Salud | `HEALTHCHECK` de Docker + `restart: unless-stopped` | 3 fallos → reinicio automático |
| Latencia | cabecera `X-Process-Time-ms` y logs `neumonia.api` | p95 > 3 s → revisar CPU/memoria |
| Errores | logs con código HTTP por petición | 5xx > 1 % → incidente |
| Recursos | `docker stats`; gráficas de DigitalOcean (CPU, RAM) con alerta por correo | RAM > 85 % |
| Deriva de datos | proporción de `label` y de `view_position` en logs/historial | cambio > 20 % semanal → reevaluar |
| Disponibilidad externa | DigitalOcean Uptime check sobre `/health` | alerta por correo |

`docker compose logs -f api` y `docker compose ps` son la primera línea de diagnóstico.

## 5. Guion de la demo en vivo (5 min)
1. Pipeline verde en GitLab (mostrar compuertas y el *deploy* manual).
2. UI pública: cargar `viral (3).dcm` → resultado, Grad-CAM, metadatos (edad 6, AP) → PDF.
3. Cargar un `.txt` → mensaje de error (422 en la API).
4. `/docs` de la API y `curl` a `/predict`.
5. MLflow: comparar dos *runs* (umbral 0.5 vs 0.35) y la sensibilidad por subgrupo.
6. Hallazgo Grad-CAM (atajos) y riesgos → cierre con el post-mortem.

## 6. Reversión
`IMAGE_TAG=<sha anterior> docker compose up -d` en el Droplet, o volver a correr `deploy-droplet` de un
pipeline anterior desde GitLab (las imágenes quedan etiquetadas por *commit*).
