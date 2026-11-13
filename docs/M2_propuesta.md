# M2 · Propuesta del proyecto — Apoyo al diagnóstico de neumonía con explicabilidad

> Peso: 35 %. Incluye Data Thinking, Business Model Canvas, OKR y KPI, problema, alcance, alternativas,
> historias de usuario con criterios de aceptación, cronograma, riesgos y tablero Kanban.

| Rol | Integrante | Responsabilidad |
|---|---|---|
| Líder / Capitán | _(nombre)_ | Alcance, cronograma, sustentaciones |
| Ingeniero(a) de ML | _(nombre)_ | Modelo, Grad-CAM, evaluación y MLflow |
| Ingeniero(a) de software | _(nombre)_ | API, UI, Docker, CI/CD |
| QA / Datos | _(nombre)_ | Pruebas, dataset, metadatos, riesgos |

---

## 1. Data Thinking
**Usuarios y contexto.** El médico general de urgencias o de atención primaria en un municipio sin
radiólogo de turno. La radiografía de tórax se toma, pero la lectura experta llega horas o días después.
La neumonía es una de las principales causas infecciosas de muerte en niños menores de 5 años en el mundo (OMS).

**Mapa de empatía (resumen).** *Piensa*: "¿estoy viendo una consolidación o es la técnica?". *Necesita*: una
segunda opinión rápida que diga **dónde** mirar. *Teme*: que la herramienta decida por él o que falle en silencio.

**Definición del problema (¿Cómo podríamos…?).**
> ¿Cómo podríamos ayudar a un médico no radiólogo a **priorizar** las radiografías de tórax con sospecha de
> neumonía, mostrando la región que motivó la sugerencia, en menos de 5 segundos y sin enviar datos del paciente fuera
> de la institución?

**Hipótesis de valor.**
1. Una sugerencia con mapa de calor reduce el tiempo hasta la decisión de tratamiento.
2. El médico confía más en una herramienta que explica (Grad-CAM) que en una probabilidad sola.
3. Un despliegue local en CPU es viable sin GPU ni nube.

**Datos disponibles (¿existen y con qué calidad?).** Modelo preentrenado del caso base y RSNA 2018 con
metadatos (ver `docs/dataset.md`). La calidad de las etiquetas (radiólogos) y la existencia de metadatos
definieron la elección.

## 2. Business Model Canvas

| Bloque | Contenido |
|---|---|
| **Segmentos de clientes** | IPS de primer y segundo nivel sin radiólogo 24/7; programas de telemedicina; docencia en radiología |
| **Propuesta de valor** | Tamizaje de neumonía en segundos, en CPU, con explicación visual, reporte PDF e historial; sin datos del paciente fuera de la institución |
| **Canales** | Aplicación web local (Streamlit), API REST/gRPC para integrar con el PACS/HIS, contenedor Docker |
| **Relación con clientes** | Implementación asistida, capacitación sobre límites del modelo, soporte por incidencias |
| **Fuentes de ingreso** | Licencia institucional anual por sede; servicio de implantación; (académico: sin ánimo de lucro) |
| **Recursos clave** | Modelo y pipeline versionados, dataset con metadatos, equipo ML + software, infraestructura CPU |
| **Actividades clave** | Validación local por sede, monitoreo de desempeño, actualización del modelo, soporte |
| **Socios clave** | IPS piloto, radiólogos validadores, universidad (UAO), proveedor de nube (DigitalOcean) |
| **Estructura de costos** | Cómputo CPU (~USD 24/mes por Droplet 2 vCPU/4 GB), horas de validación clínica, mantenimiento |

## 3. OKR y KPI

**Objetivo 1 — Entregar un servicio de apoyo diagnóstico confiable y reproducible.**
| KR | Meta | Medición |
|---|---|---|
| KR1.1 | 100 % de las compuertas de CI en verde en `main` | GitHub Actions / GitLab CI |
| KR1.2 | Cobertura de pruebas ≥ 80 % (actual: 98 %) | `make cov` |
| KR1.3 | Despliegue en Droplet accesible con demo en vivo el 28/11 | URL pública + smoke de producción |

**Objetivo 2 — Conocer honestamente el desempeño y los sesgos del modelo.**
| KR | Meta | Medición |
|---|---|---|
| KR2.1 | Sensibilidad ≥ 0.90 en RSNA (subconjunto estratificado de 500) | MLflow `recall` |
| KR2.2 | Brecha de sensibilidad entre sexos ≤ 10 puntos | MLflow `recall__sex__*` |
| KR2.3 | 20 mapas Grad-CAM revisados con la lista de chequeo de atajos | skill `gradcam-review` |

**KPI operativos (continuos).**
| KPI | Umbral | Fuente |
|---|---|---|
| Latencia p95 de `/predict` (CPU) | < 3 s | cabecera `X-Process-Time-ms` / logs |
| Disponibilidad del servicio | ≥ 99 % en la ventana de demo | `HEALTHCHECK` / monitoreo |
| Tasa de errores 5xx | < 1 % | logs de la API |
| Tasa de entradas rechazadas (422) | Seguimiento (calidad de datos de entrada) | logs de la API |

## 4. Alcance

**Dentro del alcance.** Clasificación NORMAL/PNEUMONIA (con subtipo sugerido) de radiografías frontales de tórax en
DICOM/JPG/PNG; Grad-CAM; UI clínica; API REST y gRPC; reporte PDF; historial CSV; evaluación con MLflow;
contenedores CPU; CI/CD; despliegue en Droplet.

**Fuera del alcance.** Diagnóstico autónomo; certificación como dispositivo médico (INVIMA); reentrenamiento del
modelo; integración real con PACS/HIS; radiografías laterales o pediátricas menores de 1 año; LLM (fuera de alcance del
curso).

## 5. Estado del arte (resumen)
- **CheXNet** (Rajpurkar et al., 2017): DenseNet-121 sobre ChestX-ray14, desempeño comparable a radiólogos en neumonía.
- **Kermany et al. (2018, Cell)**: *transfer learning* en radiografías pediátricas (bacteriana vs viral vs normal).
- **RSNA Challenge (2018)**: detección y localización de opacidades; las mejores soluciones usaron detectores (RetinaNet, Mask R-CNN).
- **TorchXRayVision** (Cohen et al., 2022): modelos preentrenados multi-dataset, referente para generalización.
- **Explicabilidad**: Grad-CAM es el estándar *de facto* en CNN médicas, con críticas conocidas sobre su
  fidelidad (Saporta et al., 2022, *Nature MI*): por eso se usa como herramienta de auditoría y no como prueba.

## 6. Alternativas de solución

| Alternativa | Ventajas | Desventajas | Decisión |
|---|---|---|---|
| A. **Reutilizar conv_MLP_84 + MVC + API + Grad-CAM** | Caso base comparable; foco en ingeniería (lo que evalúa el curso); CPU | Modelo de 2020 entrenado en pediatría | ✅ **Elegida** |
| B. Reentrenar una CNN (DenseNet/EfficientNet) con RSNA | Mejor generalización a adultos | Requiere GPU y semanas; no lo evalúa el curso | Trabajo futuro |
| C. TorchXRayVision preentrenado | Modelos robustos multi-dataset | Cambia el caso base; agrega PyTorch | Trabajo futuro (el DIP lo permite) |
| D. Servicio en la nube (Google Cloud Healthcare / AWS) | Escala | Datos sensibles fuera de la institución; costo; no académico | Descartada |

## 7. Matriz de riesgos (probabilidad × impacto, 1–3)

| ID | Riesgo | P | I | Nivel | Mitigación | Dueño |
|---|---|---|---|---|---|---|
| R-01 | Falso negativo: neumonía no detectada | 2 | 3 | **Alto** | Umbral configurable priorizando sensibilidad; aviso de herramienta de apoyo; supervisión humana | ML |
| R-02 | *Domain shift* (entrenado en niños, uso en adultos) | 3 | 3 | **Alto** | Evaluación en RSNA por edad; documentar en Model Card; restringir uso previsto | ML |
| R-03 | Exposición de datos del paciente (DICOM con PHI) | 2 | 3 | **Alto** | Lista blanca de metadatos; pruebas anti-fuga; sin rutas en respuestas; `.env` fuera de Git | QA |
| R-04 | Sesgo por sexo/edad/proyección | 2 | 2 | Medio | Métricas por subgrupo en cada evaluación (KR2.2) | QA |
| R-05 | Aprendizaje por atajos (marcadores, bordes) — **observado** en Grad-CAM | 3 | 2 | **Alto** | Revisión sistemática de Grad-CAM; documentado; trabajo futuro: recorte pulmonar / reentrenar | ML |
| R-06 | Modelo no disponible o alterado (118 MB fuera de Git) | 2 | 2 | Medio | Descarga con SHA-256; caché en CI; espejo en el registro de imágenes | SW |
| R-07 | Memoria insuficiente en el Droplet (TensorFlow CPU) | 2 | 2 | Medio | Droplet de 4 GB; límites en Compose; healthcheck con `start-period` | SW |
| R-08 | Credenciales filtradas en CI | 1 | 3 | Medio | Variables *Protected/Masked*; `detect-private-key`; despliegue manual | SW |
| R-09 | Dependencia de un integrante (bus factor) | 2 | 2 | Medio | Revisión cruzada en PR; skills y CLAUDE.md documentan procedimientos | Líder |
| R-10 | Retraso frente a fechas fijas del curso | 2 | 2 | Medio | Kanban con WIP; entregables mínimos primero (smoke, contrato) | Líder |

**Clasificación EU AI Act**: sistema de **alto riesgo** (componente de dispositivo médico, anexo I). Obligaciones
usadas como lista de chequeo: gestión de riesgos (esta matriz), gobernanza de datos (`docs/dataset.md`),
documentación técnica (`docs/model_card.md`), registros (`request_id`, logs), transparencia (aviso en UI/PDF),
supervisión humana (la herramienta no decide) y precisión/robustez (pruebas + evaluación por subgrupos).

## 8. Historias de usuario y criterios de aceptación (Gherkin)

**HU-01 — Clasificar una radiografía** *(Must)*
Como médico general, quiero cargar una radiografía (DICOM/JPG/PNG) y obtener NORMAL o PNEUMONIA con su probabilidad,
para priorizar la atención.
```gherkin
Dado que la API está disponible
Cuando envío "viral (3).dcm" a POST /predict
Entonces recibo 200 con label en {NORMAL, PNEUMONIA} y 0 ≤ probability ≤ 1
Y la respuesta no contiene PatientID ni rutas locales
```
*Pruebas*: `tests/test_api.py::test_predict_ok_with_course_samples`, `test_response_has_no_local_paths`.

**HU-02 — Ver por qué** *(Must)*
Como médico, quiero ver un mapa de calor sobre la radiografía para saber qué región motivó la sugerencia.
```gherkin
Cuando obtengo un resultado
Entonces gradcam_url devuelve un PNG 512×512
Y el mapa corresponde a la clase de la decisión
```
*Pruebas*: `test_gradcam_url_is_served`, `test_gradcam_targets_decided_subtype`.

**HU-03 — Reporte y trazabilidad** *(Must)*
Como médico, quiero descargar un PDF y guardar el resultado en un historial para la historia clínica.
```gherkin
Dado un resultado y el documento "1144123456"
Cuando pulso "Descargar reporte PDF"
Entonces obtengo un PDF con resultado, probabilidad, imágenes y aviso legal
Y "Guardar en historial" agrega una fila al CSV con fecha UTC
```
*Pruebas*: `tests/test_report_and_view.py`.

**HU-04 — Entradas inválidas** *(Must)*
Como integrador, quiero errores claros cuando el archivo no es una radiografía.
```gherkin
Cuando envío un archivo vacío, un .txt o un PNG corrupto
Entonces recibo 422 con detail[].msg explicando el motivo
Y si el modelo falla recibo 500 con {"error": "..."} sin trazas internas
```

**HU-05 — Metadatos sin datos personales** *(Should)*
Como médico, quiero ver edad, sexo y proyección del DICOM, sin exponer la identidad del paciente.

**HU-06 — Evaluar y comparar experimentos** *(Should)*
Como ingeniero de ML, quiero registrar en MLflow métricas globales y por subgrupo para comparar umbrales.
```gherkin
Cuando ejecuto make evaluate
Entonces MLflow registra threshold, n_samples, recall, roc_auc y recall por sexo/edad/proyección
Y guarda predictions.csv, metrics.json y ejemplos Grad-CAM
```

**HU-07 — Desplegar con un clic** *(Must, M4)*
Como equipo, quiero que un merge a `main` construya, pruebe, escanee y (con aprobación) despliegue en el Droplet.

**HU-08 — Integración gRPC** *(Could)*
Como sistema interno, quiero llamar `PneumoniaDetector/Predict` y recibir el PNG en la misma respuesta.

## 9. Cronograma (calendario oficial del curso, 16 sesiones)

| Semana | Sesiones | Módulo | Entregables del equipo |
|---|---|---|---|
| 15–24/10 | 1–5 | **M1** | Refactor MVC, uv, pytest AAA, Docker CPU, UI Streamlit, CI, PR → **sustentación M1 (31/10)** |
| 27/10–31/10 | 6–8 | **M2** | Este documento, Kanban, riesgos, historias con AC → **entrega M2 (31/10)** |
| 05/11–14/11 | 9–12 | **M3** | API FastAPI + gRPC, MLflow, dataset RSNA con metadatos, Docker Compose → **sustentación M3 (14/11)** |
| 19/11–28/11 | 13–16 | **M4** | GitLab CI/CD con compuertas, credenciales, Droplet, monitoreo, post-mortem → **sustentación M4 (28/11)** |

Hitos inmediatos: **12/11** integrar gRPC (Clase 7) y MLflow (Clase 9) · **14/11** demo local M3 ·
**21/11** pipeline GitLab verde hasta *deploy* · **26/11** ensayo de demo en producción · **28/11** sustentación final.

## 10. Tablero Kanban

**Columnas**: Backlog → Listo (con AC) → En curso (**WIP ≤ 2 por persona**) → En revisión (PR abierto) → Hecho.

**Definition of Ready**: historia con criterios de aceptación en Gherkin y estimación (S/M/L).
**Definition of Done** (M1 del curso): MVC respetado · uv + `uv.lock` · pruebas AAA verdes con cobertura ≥ 80 % ·
Docker CPU construye · UI funcional · PR revisado por otra persona · ruff limpio · documentación actualizada.

| Backlog | Listo | En curso | Revisión | Hecho |
|---|---|---|---|---|
| HU-08 gRPC en Compose | HU-07 despliegue Droplet | HU-06 evaluación RSNA 500 | — | HU-01, HU-02, HU-03, HU-04, HU-05 |
| Validar Grad-CAM con cajas RSNA (IoU) | Monitoreo (logs + alertas) | | | CI GitHub, Docker, pre-commit |
| Recorte pulmonar para mitigar R-05 | | | | Kit agéntico (CLAUDE.md, skills) |
