# Dataset: selección, justificación y datasheet

## 1. Requisito
El caso pide "un dataset de imágenes con metadatos" de calidad para validar el sistema, y el README del
curso permite dejar el enlace, la licencia y 3–5 muestras si el dataset no se puede redistribuir.

## 2. Candidatos evaluados

| Dataset | Tamaño / formato | Metadatos por imagen | Etiquetas | Licencia / acceso | Veredicto |
|---|---|---|---|---|---|
| **RSNA Pneumonia Detection Challenge (2018)** | 26 684 DICOM 1024×1024 (≈3.9 GB) | **Edad, sexo, proyección AP/PA, modalidad** en la cabecera DICOM | Normal / Lung Opacity / No Lung Opacity-Not Normal, por 6 radiólogos + **cajas** | Investigación y educación con atribución (RSNA); Kaggle con aceptación de reglas | ✅ **Principal** |
| Kermany *Chest X-Ray Images (Pneumonia)* | 5 856 JPG (≈1.2 GB) | Ninguno (solo subtipo en el nombre) | Normal / bacteriana / viral, revisadas por expertos | CC BY 4.0 (Mendeley Data) | ✅ Complementario (es la distribución de entrenamiento) |
| NIH ChestX-ray14 | 112 120 PNG (≈45 GB) | Edad, sexo, proyección en CSV | 14 hallazgos extraídos por NLP de informes (ruidosas) | Uso libre con cita (NIH) | ❌ Etiquetas ruidosas; muy grande |
| CheXpert (Stanford) | 224 316 JPG | Edad, sexo, proyección | 14 hallazgos por NLP con incertidumbre | Acuerdo de uso de investigación (registro) | ❌ Registro previo y etiquetas inciertas |
| MIMIC-CXR | 377 110 DICOM | Completos | Por NLP | PhysioNet con credencial y curso CITI | ❌ Acceso tarda semanas |
| PneumoniaMNIST (MedMNIST) | 5 856 a 28×28 | Ninguno | Normal / neumonía | CC BY 4.0 | ❌ Resolución incompatible (512×512) |

## 3. Decisión: RSNA Pneumonia Detection Challenge como dataset principal

1. **Metadatos reales en DICOM**: edad (`PatientAge`), sexo (`PatientSex`) y proyección (`ViewPosition`) vienen
   en la cabecera. Así el pipeline se prueba con el formato que pide el contrato (DICOM) y se puede evaluar la
   **equidad por subgrupo** (sexo, edad, AP/PA).
2. **Es la fuente de los DICOM del aula**: `normal (3).dcm` y `viral (3).dcm` tienen UUID de paciente RSNA,
   1024×1024, `CR`, `SeriesDescription = "view: PA"`, que es exactamente la estructura del RSNA. Usarlo
   mantiene la coherencia con el caso base.
3. **Etiquetas de expertos**: radiólogos (RSNA + Society of Thoracic Radiology) y no NLP. Es una referencia más
   confiable que ChestX-ray14 o CheXpert.
4. **Cajas delimitadoras**: permiten, como trabajo futuro, medir si Grad-CAM apunta a la opacidad
   (*pointing game* / IoU), es decir, validar la explicabilidad cuantitativamente.
5. **Distribución distinta a la de entrenamiento**: conv_MLP_84 se entrenó con radiografías pediátricas
   (Kermany, 1–5 años, Guangzhou). RSNA son mayoritariamente adultos de EE. UU.: mide la **generalización real**
   y no una métrica inflada por fuga de datos.
6. **Tamaño manejable**: se usa un subconjunto estratificado de 2 000 imágenes (`--subset 2000 --seed 42`) para
   evaluar en CPU en minutos.

**Kermany como complemento**: es el dataset del que provienen los JPG del aula y la definición de las 3 clases del
modelo (bacteriana/viral/normal). Sirve para verificar el `subtype`, pero sus métricas **no** cuentan como
generalización (posible solapamiento con el entrenamiento).

**Mapeo de etiquetas RSNA → contrato**
| Clase RSNA | `target` | Comentario |
|---|---|---|
| `Lung Opacity` | 1 (PNEUMONIA) | Opacidad compatible con neumonía (con cajas) |
| `Normal` | 0 (NORMAL) | Sin hallazgos |
| `No Lung Opacity / Not Normal` | 0 | Sin neumonía pero **con otra anormalidad**: se reporta aparte con `rsna_class` porque es el grupo más difícil |

## 4. Cómo obtenerlo
```powershell
# 1) Token de Kaggle: kaggle.com → Settings → API → Create New Token
#    Guardar en %USERPROFILE%\.kaggle\kaggle.json
# 2) Aceptar reglas: https://www.kaggle.com/competitions/rsna-pneumonia-detection-challenge/rules
cd C:\Neumonia
make dataset-rsna        # descarga, descomprime y cataloga un subconjunto estratificado de 2000
```
Sin Kaggle: RSNA publica los mismos datos en <https://www.rsna.org/education/ai-resources-and-training/ai-image-challenge/rsna-pneumonia-detection-challenge-2018>
(descarga directa de imágenes y anotaciones). Basta con dejar `stage_2_train_labels.csv`,
`stage_2_detailed_class_info.csv` y `stage_2_train_images/` en `data/raw/rsna/` y ejecutar el mismo comando.

**Salidas**: `data/processed/rsna_metadata.csv` (catálogo) y `data/processed/rsna_summary.json` (balance y demografía).

## 5. Datasheet (Gebru et al., 2021) — RSNA Pneumonia 2018

| Pregunta | Respuesta |
|---|---|
| **Motivación** | Desarrollar algoritmos de apoyo para detectar neumonía donde falta experticia radiológica (RSNA, 2018). |
| **Composición** | 30 000 radiografías frontales de ChestX-ray14 (NIH): 15 000 con hallazgos tipo neumonía, 7 500 sin hallazgos y 7 500 con otras patologías. 26 684 en el *train* público (stage 2). |
| **Recolección** | Clinical Center del NIH; selección aleatoria por etiqueta NLP; re-anotación por 6 radiólogos certificados (MD.ai). |
| **Preprocesamiento** | Convertidas a DICOM 1024×1024, 8 bits, MONOCHROME2; desidentificadas con UUID aleatorio por examen. |
| **Metadatos útiles** | `PatientAge`, `PatientSex`, `ViewPosition` (AP/PA), `Modality` (CR/DX), `BodyPartExamined`. |
| **Sesgos conocidos** | Un solo hospital (EE. UU.); las placas AP vienen de pacientes hospitalizados y concentran más positivos (riesgo de atajo "AP = enfermo"); pocos niños. |
| **Usos recomendados** | Investigación y educación en detección/localización de opacidades. |
| **Usos no recomendados** | Diagnóstico clínico sin validación local; inferir causas (bacteriana/viral): RSNA no las etiqueta. |
| **Distribución** | Kaggle (reglas de la competencia) y RSNA (atribución requerida). **No se redistribuye en este repo**: solo 2 DICOM de muestra ya presentes en el material del aula. |
| **Privacidad** | Desidentificado en origen; aun así, el lector descarta cualquier identificador (`SAFE_FIELDS`). |
| **Cita** | Shih G. et al. *Augmenting the National Institutes of Health Chest Radiograph Dataset with Expert Annotations of Possible Pneumonia*. Radiology: AI 2019;1(1):e180041. Wang X. et al. *ChestX-ray8*. CVPR 2017. |

## 6. Datos locales del aula (smoke test)
`data/JPG.zip` (12 JPG: 4 normal, 4 bacteriana, 4 viral — Kermany) y `data/DICOM.zip` (4 DICOM — RSNA).
`make data-course` los descomprime en `data/raw/course/` y genera `data/processed/course_metadata.csv`
(16 imágenes, prevalencia 62,5 %). Las 5 muestras de `artifacts/samples/` salen de estos ZIP.
