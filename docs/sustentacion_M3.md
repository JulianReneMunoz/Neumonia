# Guion de sustentación — M3 · Construcción local (sábado 14/11/2026)

> Peso: 25 %. Exige: repositorio, backend/API, pruebas con pytest y tracking con MLflow **corriendo en la máquina
> del equipo**, más calidad y Gitflow. Duración sugerida: **12 min + preguntas**.

## 0. Antes de entrar (checklist, 15 min antes)
```powershell
cd C:\Neumonia
git switch main; git pull                 # versión v0.3.0
make check                                # 309 passed, 98 %  → capturar pantalla
make evaluate                             # asegura mlflow.db con corridas
```
Ten listas, cada una en su pestaña:
- `make api` → http://localhost:8000/docs
- `make ui` → http://localhost:8501 (o 8502)
- `make mlflow` → http://127.0.0.1:5000
- GitHub: https://github.com/JulianReneMunoz/Neumonia (pestañas *Actions*, *Pull requests*, *Releases*)
- `docs/arquitectura/DESIGN.md` en VS Code con vista previa
- `graphify-out/graph.html` en el navegador

Archivos de prueba: `artifacts\samples\viral (3).dcm` y un `.txt` cualquiera (para el 422).

---

## 1. Problema y propuesta (1,5 min)
- Neumonía: priorizar radiografías cuando no hay radiólogo; el médico necesita saber **dónde mirar**.
- Solución: sugerencia NORMAL/PNEUMONIA con **Grad-CAM**, metadatos DICOM sin datos personales y reporte PDF, en CPU.
- Aclarar desde el inicio: *"Reutilizamos el modelo preentrenado del caso base; el curso evalúa contrato y despliegue,
  no la métrica (README del caso, ADR-0002)."*

## 2. Arquitectura (2,5 min) — `docs/arquitectura/DESIGN.md`
1. **Diagrama 03 (componentes)**: MVC + Estrategia + DIP. Seis interfaces `Protocol`; `factory.py` es la única que crea clases concretas.
2. **Diagrama 12 (dependencias medidas con graphify)**: *"Vista→Modelo = 0 aristas y Modelo→Controlador = 0. No lo
   afirmamos: lo mide el grafo y lo prueba `test_architecture.py` en CI."*
3. **Diagrama 05 (secuencia `/predict`)**: firma binaria → CLAHE → modelo → política de decisión → Grad-CAM.
4. Mencionar la trazabilidad: `METODOLOGIAS_ARQUITECTURA.md` relaciona las 23 metodologías con cada componente.

## 3. Demo en vivo (5 min)
| # | Acción | Qué decir / mostrar |
|---|---|---|
| 1 | UI: documento `1144123456` + `viral (3).dcm` → **Predecir** | PNEUMONIA 99,21 %, subtipo viral, metadatos (6 años, F, AP) |
| 2 | Señalar el Grad-CAM | *"Aquí el modelo mira el marcador de lateralidad y los bordes: posible atajo (riesgo R-05). Grad-CAM nos sirvió para auditar el modelo."* |
| 3 | **Descargar reporte PDF** y **Guardar en historial** | PDF generado desde datos (no captura); CSV con fecha UTC |
| 4 | API `/docs` → `POST /predict` con el DICOM | JSON del contrato: `label`, `probability`, `gradcam_url` + campos aditivos |
| 5 | `POST /predict` con un `.txt` | **422** con `detail[].msg` → contrato de errores |
| 6 | MLflow → comparar corridas umbral **0.5 vs 0.99** | Ver tabla de la sección 3.1: con 0.99 desaparece el falso positivo pero se pierden 2 neumonías |
| 7 | Terminal: `make check` (o la captura) | 309 pruebas, cobertura 98 %, ruff limpio |

### 3.1 Resultados reales del análisis de umbral (16 imágenes del aula, MLflow)
| Métrica | Umbral 0.5 | Umbral 0.99 |
|---|---|---|
| Falsos positivos | 1 | **0** |
| Falsos negativos | 0 | **2** |
| Especificidad | 0.833 | **1.000** |
| Sensibilidad | **1.000** | 0.800 |
| Exactitud | 0.9375 | 0.875 |
| AUC | 0.983 | 0.983 (no depende del umbral) |

Mensaje: *"Subir el umbral elimina falsas alarmas pero deja pasar neumonías. En tamizaje un falso negativo es más
grave, por eso el umbral por defecto es 0.5 y es configurable (`NEUMONIA_THRESHOLD`). Con 0.35 el resultado no
cambió porque el modelo está muy seguro en estas imágenes: ninguna cae entre 0.35 y 0.5."*

## 4. Calidad, Gitflow y CI (2 min) — GitHub
- **Actions**: 4 compuertas (lint → test Ubuntu + Windows → docker con smoke del contenedor). Con caché de capas, `docker` bajó de 10 min a 2 min.
- **PR #1** `fix/ci-windows-utf8`: *"el CI de Windows falló por la codificación cp1252; lo detectó la compuerta, se
  corrigió en una rama fix, PR con CI verde y merge a develop."* → evidencia de que las compuertas funcionan.
- **PR #2** `release/v0.3.0 → main` + tag **v0.3.0** → Gitflow completo.
- pre-commit (ruff, secretos, archivos grandes) y protección de `main`.

## 5. Desarrollo con agentes (1 min)
- Claude Code con `CLAUDE.md`, 10 skills, 2 subagentes y hooks que bloquean `pip`, pesos y secretos.
- **graphify** = mapa del código; **Engram** = memoria de decisiones (18 memorias). Humano aprueba cada PR
  (`docs/declaracion_uso_ia.md`).

## 6. Cierre: limitaciones y M4 (0,5 min)
- Modelo entrenado en niños → evaluar en RSNA (adultos) por subgrupos; probabilidades no calibradas; atajos.
- M4: GitLab CI/CD con Trivy, despliegue manual en Droplet, monitoreo y post-mortem (ya configurado en `.gitlab-ci.yml`).

---

## Preguntas probables y respuestas
| Pregunta | Respuesta corta | Evidencia |
|---|---|---|
| ¿Entrenaron el modelo? | No: reutilizamos `conv_MLP_84.h5`, el caso base; el curso evalúa contrato y despliegue. Se verifica su SHA-256 | README del caso §4, ADR-0002 |
| ¿Por qué sumar bacteriana + viral? | El *argmax* de 3 clases puede decir "normal" con 0.4 cuando la neumonía suma 0.6; el umbral prioriza sensibilidad | ADR-0003, `test_decision.py` |
| ¿Por qué el umbral 0.35 dio igual que 0.5? | En las 16 imágenes del aula el modelo está muy seguro (p≈0 o ≈1); ninguna cae entre 0.35 y 0.5. Con 0.99 sí cambia: especificidad 1.0 y sensibilidad 0.8 | MLflow, sección 3.1 |
| ¿Cómo garantizan MVC? | Prueba AST en CI + grafo graphify: 0 dependencias Vista→Modelo | `test_architecture.py`, diagrama 12 |
| ¿Por qué RSNA? | DICOM con edad/sexo/proyección, etiquetas de 6 radiólogos, cajas; los DICOM del aula son RSNA; mide generalización (adultos) | `docs/dataset.md`, ADR-0004 |
| ¿Las métricas de 0.94 son buenas? | Están infladas: posible solapamiento con el entrenamiento. La evaluación honesta es RSNA | Model Card |
| ¿Qué pasa con los datos del paciente? | Lista blanca de metadatos; PatientID/Name nunca salen; pruebas anti-fuga (Ley 1581/2012) | `metadata.py`, `test_api.py` |
| ¿Por qué FastAPI y gRPC? | REST para interoperabilidad pública; gRPC para clientes internos con el PNG en la misma respuesta | ADR-0005 |
| ¿Por qué SQLite en MLflow? | MLflow 3 dejó el file store en mantenimiento | ADR-0006 |
| ¿Por qué uv y no pip? | Regla del curso; lockfile multiplataforma: el mismo `uv.lock` corre en Windows, Linux y Docker | `uv.lock`, CI matriz |
| ¿Qué hizo la IA y qué el equipo? | El agente propone; CI verifica; una persona revisa y aprueba cada PR | `docs/declaracion_uso_ia.md` |
| ¿Cuánto tarda una predicción? | ≈1 s en CPU (inferencia + Grad-CAM); cabecera `X-Process-Time-ms` | API |

## Plan B si algo falla en vivo
- La UI no carga → usar `/docs` de la API.
- Sin internet → todo es local, salvo GitHub; llevar capturas de Actions, PRs y Release.
- El modelo no está → `make model` (o copiar el `.h5` del aula a `artifacts\model\`).
