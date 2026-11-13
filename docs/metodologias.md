# Metodologías del proyecto y razones de su elección

> Proyecto Neumonía — Gestión de Proyectos en IA y CD · UAO 2026-2S · caso base del curso.
> Cada metodología se describe con el mismo formato: **qué es**, **cómo se aplica aquí** (con los
> archivos donde se ve), **por qué se eligió** y **qué alternativa se descartó**.

## Mapa general

| # | Metodología | Ámbito | Dónde se ve | Razón principal |
|---|---|---|---|---|
| 1 | CRISP-DM (+ MLOps) | Ciclo de vida | toda la estructura | Marco del curso; fases auditables |
| 2 | Data Thinking | Descubrimiento | `docs/M2_propuesta.md` | Problema antes que modelo |
| 3 | DAMA-DMBOK | Gobierno de datos | `data/`, `model/metadata.py`, `docs/dataset.md` | Calidad, metadatos, privacidad |
| 4 | Kanban (Scrumban) | Gestión ágil | `docs/M2_propuesta.md` §8 | Equipo pequeño con fechas fijas |
| 5 | BMC + OKR/KPI | Valor | `docs/M2_propuesta.md` §2–3 | Exigido en M2; medible |
| 6 | Gestión de riesgos + EU AI Act | Riesgo | `docs/M2_propuesta.md` §7 | Sistema de IA médico = alto riesgo |
| 7 | MVC | Arquitectura | `src/neumonia/{model,controller,view}` | DoD del M1 |
| 8 | SOLID: Estrategia + DIP | Diseño | `readers.py`, `decision.py`, `classifier.py`, `gateways.py` | Patrones exigidos en la Clase 1 |
| 9 | Humble Object | Diseño de UI | `view/presenter.py` | UI probable sin navegador |
| 10 | Contract-first (OpenAPI) + REST/gRPC | Integración | `api/openapi.yaml`, `grpc_api/` | Contrato estable del curso |
| 11 | Pirámide de pruebas + AAA + fitness functions | Calidad | `tests/` | DoD del M1; arquitectura verificable |
| 12 | Reproducibilidad (uv, 12-factor, Docker) | Entorno | `pyproject.toml`, `uv.lock`, `docker/` | "Funciona en mi máquina" no es entregable |
| 13 | Gitflow + Conventional Commits + SemVer | Versionamiento | `.github/`, `.gitlab/`, skill `gitflow-pr` | DoD del M1 |
| 14 | CI/CD con compuertas + DevSecOps | Entrega | `.github/workflows/ci.yml`, `.gitlab-ci.yml` | M1 y M4 |
| 15 | Reutilizar modelo preentrenado | Modelado | `artifacts/model/`, `model/download.py` | El curso evalúa contrato, no métrica |
| 16 | Paridad entrenamiento-servicio (CLAHE) | Preprocesamiento | `model/preprocessing.py` | Evitar *training-serving skew* |
| 17 | Análisis de decisión (umbral 3→2 clases) | Regla de negocio | `controller/decision.py`, ADR-0003 | Contrato binario; priorizar sensibilidad |
| 18 | Grad-CAM (XAI) | Explicabilidad | `model/gradcam.py` | Rápido, nativo en CNN, exigido |
| 19 | Evaluación por subgrupos + muestreo estratificado | Evaluación | `evaluation.py`, `data/dataset.py` | Equidad y reproducibilidad |
| 20 | MLOps con MLflow | Experimentación | `tracking/`, `scripts/evaluate.py` | Exigido en M3; trazabilidad |
| 21 | Model Card + Datasheet | Documentación responsable | `docs/model_card.md`, `docs/dataset.md` | Transparencia de límites |
| 22 | Privacidad desde el diseño | Ética/legal | `model/metadata.py`, `report.py` | Ley 1581/2012 (Habeas Data) |
| 23 | Desarrollo dirigido por especificaciones con agentes | Proceso | `CLAUDE.md`, `.claude/`, `specs/` | Productividad con control humano |

---

## A. Gestión del proyecto y del ciclo de vida

### 1. CRISP-DM, ampliado con prácticas de MLOps
**Qué es.** *Cross-Industry Standard Process for Data Mining*: seis fases iterativas — comprensión del
negocio, comprensión de los datos, preparación, modelado, evaluación y despliegue.

**Cómo se aplica.**
| Fase | Artefacto en el repo |
|---|---|
| Negocio | `docs/M2_propuesta.md` (problema, Data Thinking, BMC, OKR) |
| Datos | `docs/dataset.md`, `scripts/fetch_dataset.py`, `data/processed/*_summary.json` |
| Preparación | `model/readers.py`, `model/preprocessing.py`, `data/dataset.py` |
| Modelado | `conv_MLP_84.h5` reutilizado (ver §15) |
| Evaluación | `evaluation.py`, `scripts/evaluate.py` + MLflow |
| Despliegue | `api/`, `docker/`, `.gitlab-ci.yml` |

**Por qué.** Es el marco de referencia del curso (Clase 1), es neutral respecto a la herramienta y
obliga a empezar por el negocio, no por el modelo. Sus fases se mapean 1:1 a los módulos M2–M4.

**Límite reconocido y cómo se cubre.** CRISP-DM termina en "despliegue" y no trata la operación
continua (versionado de modelos, monitoreo, reentrenamiento). La Clase 1 señala ese límite "en la era
del MLOps". Por eso se complementa con MLOps (§14, §20) y con la lección de Sculley et al. (2015):
el modelo es una parte pequeña del sistema y el resto (configuración, datos, servicio, monitoreo) es lo que
acumula deuda técnica.

**Alternativas descartadas.** *TDSP* de Microsoft: muy atado a Azure y con roles pensados para equipos
grandes. *KDD/SEMMA*: centrados en el análisis, sin fase de negocio ni de despliegue.

### 2. Data Thinking
**Qué es.** Adaptación del *Design Thinking* a proyectos de datos: empatizar con el usuario, definir el
problema, idear casos de uso de datos, prototipar y probar.

**Cómo se aplica.** `docs/M2_propuesta.md` §1: mapa de actores (radiólogo, médico general de
urgencias, paciente), definición del problema ("¿cómo podríamos priorizar las radiografías con sospecha
de neumonía cuando no hay un radiólogo disponible?") e hipótesis de valor que se validan con la demo.

**Por qué.** Es exigido en el M2 y evita el error más común en IA: construir un modelo exacto para
un problema que nadie tiene. Aquí, por ejemplo, llevó a priorizar **sensibilidad** y **explicabilidad**
sobre la exactitud global: el usuario es un médico no especialista que necesita saber *dónde* mirar.

**Alternativa descartada.** *Design Thinking* puro: no incluye la pregunta "¿existen los datos y con qué
calidad?", que en este proyecto decidió el dataset (§3).

### 3. DAMA-DMBOK (gobierno de datos)
**Qué es.** Cuerpo de conocimiento de gestión de datos de DAMA International; sus áreas incluyen calidad,
metadatos, seguridad, arquitectura y gobierno de datos.

**Cómo se aplica.**
- **Metadatos**: catálogo `data/processed/<fuente>_metadata.csv` con columnas documentadas y resumen
  `*_summary.json` (balance de clases, sexo, edad, proyección).
- **Calidad**: validación en la entrada (firma binaria, imágenes vacías, MONOCHROME1, 16 bits) en `readers.py`.
- **Seguridad y privacidad**: lista blanca `SAFE_FIELDS`; PatientID y PatientName nunca salen del lector.
- **Linaje y licencias**: `docs/dataset.md` registra origen, versión, cita y licencia de cada fuente; el
  modelo se identifica por URL + SHA-256.

**Por qué.** Es el marco de datos que propone el curso y aporta un vocabulario para justificar
decisiones que en un proyecto médico no son opcionales (privacidad, trazabilidad).

**Alternativa descartada.** Un gobierno informal ("los datos están en una carpeta"): no deja
evidencia auditable ni sobrevive a la rotación del equipo.

### 4. Kanban (con cadencia Scrumban)
**Qué es.** Método ágil de flujo continuo: tablero visual, límites de trabajo en curso (WIP) y
política explícita de "terminado". Scrumban agrega una cadencia fija de revisión.

**Cómo se aplica.** Tablero en GitLab Issues / GitHub Projects con columnas
*Backlog → Listo → En curso (WIP 2 por persona) → Revisión (PR) → Hecho*. La revisión semanal coincide con
las sesiones de los sábados. La *Definition of Done* es la del M1 (ver `docs/M2_propuesta.md` §8).

**Por qué.** El equipo tiene como máximo 4 personas con dedicación parcial y fechas de entrega fijadas por el
curso (14/11 y 28/11). Los *sprints* de Scrum suman ceremonias que no caben en ese tiempo; Kanban hace visible el
cuello de botella real, que en este proyecto es la revisión de PR, y lo controla con límites de WIP.

**Alternativa descartada.** Scrum completo: planificación, *daily*, revisión y retrospectiva por
*sprint* consumen tiempo que un equipo de dedicación parcial no tiene. Cascada: incompatible con
entregas incrementales M1→M4.

### 5. Business Model Canvas, OKR y KPI
**Qué son.** BMC: lienzo de 9 bloques para describir cómo una solución crea, entrega y captura valor.
OKR: objetivos cualitativos con 3–4 resultados clave medibles. KPI: indicadores operativos continuos.

**Cómo se aplican.** `docs/M2_propuesta.md` §2 (BMC) y §3 (OKR/KPI). Ejemplo: *KR1: sensibilidad ≥ 0.90 en
el subconjunto RSNA de 500 imágenes*; *KPI: latencia p95 de /predict < 3 s en CPU*.

**Por qué.** Son exigidos en el M2 y conectan la técnica con el valor. Un KR medible convierte
"funciona bien" en una compuerta verificable en MLflow.

### 6. Gestión de riesgos (ISO 31000) y clasificación EU AI Act
**Qué es.** Identificar, analizar (probabilidad × impacto), tratar y monitorear riesgos. El *EU AI Act*
(Reglamento UE 2024/1689) clasifica los sistemas de IA por riesgo; un componente de apoyo diagnóstico es
**alto riesgo** por estar ligado a dispositivos médicos.

**Cómo se aplica.** Matriz de riesgos en `docs/M2_propuesta.md` §7 con dueño y mitigación. Las
obligaciones de alto riesgo se usan como lista de chequeo aunque el proyecto sea académico:
gobernanza de datos (art. 10, §3), documentación técnica (Model Card), registro de eventos (logs y
`request_id`), transparencia (aviso en la UI y el PDF) y supervisión humana (la herramienta *sugiere*, no decide).

**Por qué.** El dominio es médico. El hallazgo de Grad-CAM (§18) mostró además un riesgo técnico concreto
(atajos) que solo aparece si se buscan riesgos de forma sistemática.

---

## B. Ingeniería de software para IA

### 7. Modelo-Vista-Controlador (MVC)
**Qué es.** Separa la lógica de dominio (Modelo), la presentación (Vista) y la orquestación (Controlador).

**Cómo se aplica.**
- **Modelo** (`model/`): lectura DICOM/JPG, preprocesamiento, red Keras, Grad-CAM, metadatos.
- **Controlador** (`controller/`): `PneumoniaService` orquesta *leer → preprocesar → predecir → explicar*;
  `decision.py` aplica la regla de negocio; `factory.py` compone; `report.py` genera PDF/CSV.
- **Vista** (`view/`): Streamlit clínico. La API REST y gRPC son **adaptadores de entrega** adicionales
  sobre el mismo controlador.

**Por qué.** Es la primera regla de la *Definition of Done* del M1. El monolito original
(`detector_neumonia.py`, 251 líneas) mezclaba Tkinter, TensorFlow 1 y el CSV en un archivo: no se podía probar ni
desplegar. Con MVC la misma lógica sirve a tres interfaces (Streamlit, REST, gRPC) sin duplicarse.

**Cómo se garantiza.** `tests/test_architecture.py` analiza los `import` con AST y falla si la vista importa
el modelo, TensorFlow u OpenCV, o si el modelo importa la API. Es una *fitness function* (Ford et al.,
*Building Evolutionary Architectures*).

**Alternativa descartada.** Arquitectura hexagonal completa (puertos y adaptadores): es más general,
pero su vocabulario agrega complejidad sin beneficio para un equipo de 4 personas. Se toma solo su idea
clave (adaptadores REST/gRPC alrededor del núcleo).

### 8. SOLID: patrón Estrategia e Inversión de Dependencias (DIP)
**Qué es.** *Estrategia*: familia de algoritmos intercambiables detrás de una interfaz. *DIP*: los módulos de
alto nivel dependen de abstracciones, no de implementaciones concretas.

**Cómo se aplica (cuatro puntos de variación).**
| Interfaz (`Protocol`) | Implementaciones | Qué permite |
|---|---|---|
| `ImageReader` | `DicomReader`, `RasterReader` | Nuevo formato = nueva clase (abierto/cerrado) |
| `Classifier` | `KerasClassifier`, `FakeClassifier` (pruebas) | Cambiar a ONNX/PyTorch sin tocar el controlador |
| `DecisionPolicy` | `ThresholdPolicy` | Otra regla (p. ej. triage de 3 niveles) |
| `PredictionGateway` | `LocalGateway`, `HttpGateway` | La UI corre sola o contra la API (Docker) |
| `Tracker` | `MlflowTracker`, `NullTracker` | Evaluar sin MLflow instalado |

`controller/factory.py` es la **raíz de composición**: el único lugar que conoce las clases concretas.

**Por qué.** La Clase 1 los nombra explícitamente (Estrategia + DIP, cohesión y acoplamiento). Su
beneficio medible: **331 de las 340 pruebas corren sin cargar el modelo de 118 MB**, porque el controlador
recibe dobles de prueba.

**Alternativa descartada.** Un contenedor de inyección de dependencias (p. ej. `dependency-injector`):
dependencia extra para algo que un constructor resuelve.

### 9. Humble Object (presentador)
**Qué es.** Dejar el código difícil de probar (widgets) lo más "tonto" posible y mover la lógica a un objeto
probable.

**Cómo se aplica.** `view/presenter.py` decide titulares, colores, formato de porcentajes y validación del
documento; `streamlit_app.py` solo dibuja. Se prueba con pytest y con `streamlit.testing.AppTest`.

**Por qué.** Las pruebas de UI con navegador son lentas y frágiles; así la lógica de la vista queda cubierta.

### 10. Contract-first API (OpenAPI), REST y gRPC
**Qué es.** Definir primero el contrato (esquema de entrada y salida, errores) y después implementarlo.

**Cómo se aplica.** `api/openapi.yaml` es la fuente de verdad: `label`, `probability`, `gradcam_url`
estables; campos nuevos solo aditivos; `422` con `detail` y `500` con `{error}`. FastAPI genera `/docs` y valida
con Pydantic. gRPC (`neumonia.proto`, Clase 7) ofrece el mismo servicio con el PNG embebido.

**Por qué.** El curso evalúa "un contrato claro". El contrato estable permite cambiar el modelo por
dentro sin romper a los clientes (UI, gRPC, pruebas de contenedor). REST se eligió como interfaz pública
por interoperabilidad; gRPC para clientes internos de baja latencia (protobuf binario, HTTP/2).

### 11. Pirámide de pruebas, patrón AAA y *fitness functions*
**Qué es.** Muchas pruebas unitarias rápidas, menos de integración y pocas de extremo a extremo. Cada prueba se
organiza en *Arrange / Act / Assert*.

**Cómo se aplica.** 340 pruebas, cobertura 99 %:
- Unitarias: lectores, metadatos, preprocesamiento, decisión, métricas, presentador.
- Integración: API con `TestClient`, gRPC en proceso, Keras mínimo real (`tiny_keras_model`), MLflow con SQLite.
- Extremo a extremo: modelo real (`-m model`), `smoke_infer.py`, `scripts/container_smoke.py` contra el contenedor.
- Arquitectura: `test_architecture.py`.
Marcas `model` y `slow` para el ciclo rápido (`make test-fast`). Compuerta `--cov-fail-under=80`.

**Por qué.** Son exigidas en el M1 (pytest AAA). La pirámide mantiene la retroalimentación en segundos
(el ciclo rápido tarda unos 15 s) y las pruebas de contenedor verifican lo que el curso califica: que el artefacto
**carga, infiere, se prueba, se contenedoriza y se despliega**.

### 12. Reproducibilidad: uv, configuración 12-factor y Docker
**Qué es.** Todo lo necesario para reproducir la ejecución está declarado y bloqueado.

**Cómo se aplica.**
- `uv` + `pyproject.toml` + `uv.lock` (Python 3.13 fijado en `.python-version`); prohibido `pip` y
  `requirements.txt` (el hook `guard_bash.py` lo bloquea para los agentes).
- Configuración por variables de entorno (`config.py`, *12-factor app*), con validación.
- Modelo identificado por URL + SHA-256; descarga atómica (`.part` → rename).
- Docker multi-etapa CPU, usuario no root, `HEALTHCHECK`, sin CUDA.

**Por qué.** Regla del curso (uv obligatorio) y condición de cualquier despliegue. `uv` resuelve e instala
entre 10 y 100 veces más rápido que pip y su *lockfile* es multiplataforma: el mismo `uv.lock`
instala TensorFlow 2.21 en Windows (`C:\Neumonia`), Linux (CI) y Docker.

**Alternativas descartadas.** Conda (pesado, *solver* lento, no exigido); Poetry (más lento, no es el estándar del curso).

### 13. Gitflow, Conventional Commits y versionado semántico
**Qué es.** Ramas `main`/`develop`/`feature`/`release`/`hotfix`; mensajes `tipo(ámbito): resumen`; versiones `MAJOR.MINOR.PATCH`.

**Cómo se aplica.** Skill `gitflow-pr`, plantillas de PR/MR, revisión humana obligatoria, tags por
entrega (`v0.1.0` M1, `v0.3.0` M3, `v1.0.0` M4). MAJOR cambia solo si se rompe el contrato.

**Por qué.** Exigido en el M1 (PRs, Gitflow). Gitflow encaja con entregas por módulo con fecha: `release/*`
congela lo que se sustenta mientras `develop` sigue avanzando.

**Alternativa descartada.** *Trunk-based development*: es mejor con despliegue continuo y equipos maduros,
pero requiere *feature flags* y disciplina de integración diaria que el curso no exige.

### 14. CI/CD con compuertas de calidad y DevSecOps
**Qué es.** Integración y entrega continuas donde cada etapa es una compuerta que detiene el pipeline si falla.

**Cómo se aplica.**
- *Shift-left*: `pre-commit` (ruff, formato, archivos grandes, llaves privadas, `uv.lock`).
- GitHub Actions (M1): ruff → pytest en Ubuntu **y Windows** con cobertura ≥ 80 % y smoke → build Docker → smoke del contenedor.
- GitLab CI (M4): ruff (code quality) → pytest (JUnit + Cobertura) → build + smoke + push al registro →
  **Trivy** (CVE críticas) → despliegue **manual** en Droplet con variables protegidas → smoke en producción.

**Por qué.** M1 pide GitHub Actions y ruff; M4 pide GitLab CI/CD con compuertas, manejo de credenciales y
despliegue. La aprobación manual del despliegue es una forma de supervisión humana (EU AI Act).

---

## C. Datos, modelo y MLOps

### 15. Reutilizar el modelo preentrenado `conv_MLP_84` (no reentrenar)
**Qué es.** Usar como artefacto el modelo ya entrenado del caso base, en lugar de entrenar uno nuevo.

**Cómo se aplica.** Descarga verificada desde el Release público `modelo-v1`
(SHA-256 `d9548ff6…e18e`, 118 MB, 9,8 M de parámetros, entrada 512×512×1, salida softmax de 3 clases).

**Por qué.** (a) El curso lo indica explícitamente: *"el M1 evalúa el contrato y el despliegue, no la
métrica"*. (b) Es el modelo del profesor, así que los resultados son comparables entre equipos. (c) Entrenar
una CNN en CPU no aporta a los criterios de evaluación y consumiría el tiempo del proyecto. El
diseño DIP (§8) deja abierta la puerta a reemplazarlo (p. ej. DenseNet-121 de TorchXRayVision) sin
tocar la API.

**Alternativas evaluadas.** Modelos públicos de Hugging Face (*ViT* o *ResNet* afinados en Kermany): contrato de 2
clases, licencias heterogéneas y menos documentación. TorchXRayVision: excelente, pero agrega PyTorch y cambia el
caso base del curso. Queda como trabajo futuro.

### 16. Paridad entrenamiento-servicio (preprocesamiento con CLAHE)
**Qué es.** Aplicar en producción exactamente la misma transformación que se usó para entrenar.

**Cómo se aplica.** `preprocessing.py`: redimensionar a 512 → escala de grises → **CLAHE**
(*Contrast Limited Adaptive Histogram Equalization*, clip 2.0, rejilla 4×4) → /255 → tensor
`(1, 512, 512, 1)`. Las pruebas fijan la forma, el tipo y el rango.

**Por qué.** El *training-serving skew* es una deuda técnica clásica (Sculley et al., 2015): un cambio
aparentemente inocuo (otro tamaño, otra normalización) degrada el modelo sin que nada falle. CLAHE mejora el
contraste local de las radiografías y fue parte del entrenamiento original, por eso no se toca.

### 17. Análisis de decisión: de 3 clases a un contrato binario
**Qué es.** Convertir probabilidades en una decisión con una regla explícita y documentada.

**Cómo se aplica.** `ThresholdPolicy`: `P(neumonía) = P(bacteriana) + P(viral)`; `PNEUMONIA` si
`P(neumonía) ≥ umbral` (0.5 por defecto, configurable con `NEUMONIA_THRESHOLD`). `subtype` conserva la clase
original y Grad-CAM se calcula sobre la clase de la decisión. Detalle en `docs/adr/0003-politica-decision.md`.

**Por qué.** Tomar el *argmax* de 3 clases da resultados incoherentes: `(0.3, 0.4, 0.3)` diría "normal" aunque
la neumonía acumula 0.6. El umbral configurable permite favorecer la **sensibilidad**, porque en tamizaje un falso
negativo (un paciente enfermo enviado a casa) cuesta más que un falso positivo (una segunda lectura).

### 18. Grad-CAM como técnica de explicabilidad
**Qué es.** *Gradient-weighted Class Activation Mapping* (Selvaraju et al., 2017): pondera los mapas de la última
capa convolucional con el promedio de los gradientes de la clase y produce un mapa de calor.

**Cómo se aplica.** `gradcam.py` con `tf.GradientTape` sobre `conv10_thisone` (31×31×128), superpuesto con
colormap JET (α = 0.8). Se corrigieron dos problemas del monolito: usaba la API de TF1 (`K.gradients`,
que ya no existe en Keras 3) y ponderaba solo 64 de los 128 filtros.

**Por qué.** Es el requisito del caso, no necesita reentrenar y cuesta una sola pasada hacia atrás (≈1 s en CPU).
Además produce una imagen que un médico entiende.
- *LIME* o *SHAP*: requieren cientos de evaluaciones del modelo por imagen, lo que no es viable en CPU.
- *Saliency maps*: son ruidosos.
- *Score-CAM*: es más fiel, pero N veces más lento.

**Hallazgo.** En `viral (3).dcm` el calor cae sobre el marcador de lateralidad y los bordes de la placa
(`docs/img/gradcam_viral.png`). Es una señal de **aprendizaje por atajos** que se documenta como riesgo R-05:
Grad-CAM sirvió para auditar el modelo, no solo para decorar la UI.

### 19. Evaluación por subgrupos y muestreo estratificado
**Qué es.** Medir el desempeño globalmente y por sexo, grupo de edad y proyección (AP/PA), con submuestras que
conservan la prevalencia.

**Cómo se aplica.** `evaluation.py` calcula exactitud, precisión, sensibilidad, especificidad, F1 y AUC.
La AUC se obtiene por el estadístico de Mann-Whitney, implementado y probado sin scikit-learn. Además calcula
la sensibilidad de cada subgrupo. `stratified_subset(seed=42)` garantiza que la submuestra se pueda
reproducir.

**Por qué.** Los metadatos DICOM del RSNA (edad, sexo, proyección) son la razón para elegir ese dataset (§3,
`docs/dataset.md`): permiten detectar sesgos, una obligación de la gestión de riesgos en IA médica. Además, el
modelo se entrenó con niños de 1 a 5 años (Kermany), y evaluarlo con adultos del RSNA mide honestamente el
cambio de distribución (*domain shift*).

### 20. MLOps con MLflow
**Qué es.** Registro de experimentos: parámetros, métricas, artefactos y versión del modelo por cada ejecución.

**Cómo se aplica.** `MlflowTracker` (backend `sqlite:///mlflow.db`; el *file store* está en mantenimiento en
MLflow 3), `make evaluate`, `make mlflow`, servicio `mlflow` en Docker Compose (perfil `mlops`).
Se registran el umbral, el dataset, `model_version`, las métricas globales y por subgrupo, `predictions.csv`,
`metrics.json` y ejemplos de Grad-CAM.

**Por qué.** Es exigido en el M3 (*tracking* con MLflow). Convierte cada afirmación de la Model Card en un
`run_id` verificable y permite comparar umbrales o modelos lado a lado. Se eligió sobre Weights & Biases
porque no requiere cuenta en la nube y corre localmente; y sobre DVC porque el problema aquí es registrar
experimentos, no versionar datasets.

### 21. Model Card y Datasheet for Datasets
**Qué es.** Fichas estandarizadas del modelo (Mitchell et al., 2019) y del dataset (Gebru et al., 2021):
uso previsto, datos, métricas, limitaciones y consideraciones éticas.

**Cómo se aplica.** `docs/model_card.md` y `docs/dataset.md`.

**Por qué.** Es la documentación técnica que pide el EU AI Act para sistemas de alto riesgo y la respuesta
honesta a "¿para qué *no* sirve este modelo?".

### 22. Privacidad desde el diseño
**Qué es.** Proteger los datos personales por defecto, minimizando lo que se recolecta y se expone.

**Cómo se aplica.** Lista blanca de metadatos (`SAFE_FIELDS`), lista negra verificada en pruebas
(`FORBIDDEN_FIELDS`), documento del paciente saneado en CSV/PDF, respuestas sin rutas locales, `.env` y
`kaggle.json` bloqueados.

**Por qué.** Los datos de salud son **datos sensibles** según la Ley 1581 de 2012 (Habeas Data, Colombia), y los
DICOM traen el nombre y el ID del paciente en la cabecera. Minimizar es más barato y más seguro que proteger
después.

---

## D. Desarrollo asistido por agentes de consola

### 23. Desarrollo dirigido por especificaciones con Claude Code
**Qué es.** Usar un agente de código en la terminal guiado por memoria del proyecto, especificaciones
verificables y compuertas automáticas, con revisión humana de cada cambio.

**Cómo se aplica.**
| Pieza | Archivo | Función |
|---|---|---|
| Memoria del proyecto | `CLAUDE.md`, `AGENTS.md` | Arquitectura, comandos, reglas y prohibiciones |
| Skills | `.claude/skills/*/SKILL.md` (10) | Procedimientos repetibles: feature MVC, pruebas AAA, contrato, dataset, MLflow, Grad-CAM, Gitflow, Docker, entregables y graphify |
| Subagentes | `.claude/agents/` | `revisor-arquitectura` (solo lectura) y `escritor-pruebas` |
| Hooks | `.claude/hooks/` | Formatear con Ruff tras cada edición; bloquear `pip`, pesos, secretos y *push* forzado |
| Permisos | `.claude/settings.json` | Permitir `uv`/`make`/`git` de lectura; preguntar antes de `push`/`merge`; negar `.env` |
| Especificaciones | `specs/*.md` | Criterios de aceptación que el agente convierte en pruebas |
| Diseño | `docs/arquitectura/DESIGN.md` + 12 diagramas | Fase *design* del flujo spec → design → tasks: cómo se construye lo especificado |
| Mapa del código (graphify) | `graphify-out/`, skill `graphify`, hooks | Grafo de 1 025 nodos que el agente consulta antes de leer archivos; verifica las dependencias entre capas |
| Memoria (Engram) | `.engram/`, `scripts/engram_memoria.py` | 19 decisiones y hallazgos que el agente recupera entre sesiones para no re-litigar ADR |

**Por qué.**
- El curso promueve agentes de código en terminal (Antigravity CLI, OpenCode, Cursor).
- Las skills codifican **una vez** el procedimiento correcto, así que el agente y el equipo siguen las mismas reglas.
- Los hooks y las pruebas de arquitectura hacen que las reglas **no dependan de la memoria** del agente ni de la
  disciplina humana.
- El ciclo *spec → prueba → código → compuerta* mantiene al humano como responsable: el agente propone, CI
  verifica y una persona aprueba el PR (`docs/declaracion_uso_ia.md`).

---

## Referencias
- Chapman, P. et al. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*.
- DAMA International (2017). *DAMA-DMBOK: Data Management Body of Knowledge*, 2.ª ed.
- Sculley, D. et al. (2015). *Hidden Technical Debt in Machine Learning Systems*. NeurIPS.
- Huyen, C. (2022). *Designing Machine Learning Systems*. O'Reilly (cap. 1–2).
- Gamma, E. et al. (1994). *Design Patterns* (Strategy). Martin, R. C. (2017). *Clean Architecture* (DIP).
- Selvaraju, R. R. et al. (2017). *Grad-CAM: Visual Explanations from Deep Networks*. ICCV.
- Pasa, F. et al. (2019). *Efficient Deep Network Architectures for Fast Chest X-Ray Tuberculosis Screening and Visualization*. Sci. Reports.
- Mitchell, M. et al. (2019). *Model Cards for Model Reporting*. FAT\*. Gebru, T. et al. (2021). *Datasheets for Datasets*. CACM.
- Shih, G. et al. (2019). *Augmenting the NIH Chest Radiograph Dataset with Expert Annotations of Possible Pneumonia*. Radiology: AI.
- Kermany, D. et al. (2018). *Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning*. Cell.
- Reglamento (UE) 2024/1689 (*AI Act*). Ley Estatutaria 1581 de 2012 (Colombia).
- AWS (2023). *Well-Architected Framework — Machine Learning Lens*.
