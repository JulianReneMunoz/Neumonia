# Model Card — conv_MLP_84 (apoyo al diagnóstico de neumonía)

Formato de Mitchell et al. (2019), *Model Cards for Model Reporting*.

## Detalles del modelo
| Campo | Valor |
|---|---|
| Nombre / versión | `conv_MLP_84` · `conv_MLP_84@modelo-v1` |
| Tipo | CNN con conexiones *skip* (5 bloques conv + AvgPool + 3 densas), basada en Pasa et al. (2019) |
| Parámetros | 9 796 483 |
| Entrada | `(1, 512, 512, 1)` float32 en [0, 1] tras gris + CLAHE (clip 2.0, 4×4) |
| Salida | softmax de 3 clases: `bacteriana`, `normal`, `viral` |
| Capa Grad-CAM | `conv10_thisone` (31×31×128) |
| Origen | Caso base UAO-Neumonía (Torres Revelo y Díaz Salazar), usado por el curso GPIA UAO 2026-2S |
| Artefacto | Release `modelo-v1` · SHA-256 `d9548ff6fd2c29cdd15328ff95e1ad1fc8c7226e04e86c5890526bea2215e18e` · 118 MB |
| Framework | Keras 3 / TensorFlow 2.21 (CPU) |
| Licencia | Uso académico |

## Uso previsto
- **Sí**: herramienta académica de **apoyo** y demostración de ingeniería de ML (contrato, pruebas, despliegue);
  tamizaje que sugiere priorizar una lectura experta, con explicación visual.
- **No**: diagnóstico autónomo, decisiones terapéuticas, radiografías laterales, otras modalidades (TC), población
  fuera de la de entrenamiento sin validación local. No es un dispositivo médico certificado (INVIMA / FDA / CE).

## Regla de decisión (contrato)
`P(neumonía) = P(bacteriana) + P(viral)`; `PNEUMONIA` si `≥ 0.5` (configurable con `NEUMONIA_THRESHOLD`).
`subtype` es una sugerencia **no validada**: RSNA no etiqueta causa bacteriana/viral.

## Datos
- **Entrenamiento (según el caso base)**: radiografías pediátricas de Kermany et al. (2018), 1–5 años,
  Guangzhou Women and Children's Medical Center, 3 clases.
- **Evaluación**: (1) 16 imágenes del aula (smoke); (2) **RSNA Pneumonia 2018**, subconjunto estratificado con
  metadatos de edad, sexo y proyección (`docs/dataset.md`).

## Métricas
Corrida de referencia: `make evaluate` (MLflow, experimento `neumonia-evaluacion`, umbral 0.5).

| Conjunto | n | Exactitud | Sensibilidad | Especificidad | AUC | Nota |
|---|---|---|---|---|---|---|
| Aula (12 JPG Kermany + 4 DICOM RSNA) | 16 | 0.94 | 1.00 | 0.83 | 0.98 | **Inflada**: posible solapamiento con el entrenamiento; solo smoke |
| RSNA subconjunto estratificado | 500 | _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ | Ejecutar `make dataset-rsna` + `scripts/evaluate.py --limit 500` y registrar el `run_id` |

Se reportan además, en MLflow, la sensibilidad por `sex`, `age_group` y `view_position`.
Latencia medida en CPU (2 vCPU): ≈ 0.5 s de inferencia + ≈ 0.5 s de Grad-CAM por imagen; carga inicial ≈ 1 s.

## Análisis cualitativo (Grad-CAM)
- En la muestra bacteriana el mapa cubre los campos pulmonares (comportamiento esperado).
- En `viral (3).dcm` (RSNA, AP, 6 años, placa rotada) el calor se concentra en el **marcador de lateralidad** y
  en los **bordes** de la placa (`docs/img/gradcam_viral.png`): evidencia de posible **aprendizaje por atajos**
  (R-05). La predicción puede ser "correcta por la razón equivocada".
- `NORMAL2-IM-1147-0001.jpeg` (normal) se clasifica como PNEUMONIA/viral con 0.98: falso positivo con alta
  confianza → la probabilidad **no está calibrada**.

## Consideraciones éticas y limitaciones
1. **Cambio de dominio**: entrenado en niños de un solo hospital chino; el uso en adultos u otros equipos requiere
   validación local (riesgo R-02).
2. **Sesgo potencial** por sexo, edad y proyección AP/PA (las AP concentran pacientes hospitalizados).
3. **Calibración**: las probabilidades son puntajes softmax, no frecuencias; no interpretar 0.98 como "98 % de certeza".
4. **Explicabilidad**: Grad-CAM muestra *dónde* miró la red, no *por qué* es correcta. Tiene baja resolución (31×31).
   El **informe de hallazgos por zonas** y las **vistas 3D** (v0.4.0, ADR-0007) resumen esa atención: no son una
   segmentación de lesiones ni una reconstrucción anatómica (una radiografía es 2D), y las zonas son geométricas
   aproximadas (menos exactas en placas rotadas o recortadas). La alerta de atajo (razón de densidad fuera/dentro
   ≥ 1.0) se activa en 3 de las 5 muestras del curso, entre ellas `viral (3).dcm` (1.04).
   Con la **segmentación pulmonar opcional** (v0.5.0, ADR-0008, PSPNet de TorchXRayVision) las zonas siguen la
   silueta real; en 4 de 5 muestras supera el control de calidad. La consolidación densa tiende a quedar fuera
   de la máscara: en `viral (3).dcm` se descarta y se usan zonas geométricas, y el informe lo indica.
5. **Privacidad**: el sistema descarta PatientID/PatientName y no los registra; el documento del paciente
   solo se guarda en el historial local si el médico lo decide.
6. **Supervisión humana**: toda salida va acompañada del aviso "no reemplaza el criterio de un profesional".

## Recomendaciones
- Validar en RSNA y en datos locales antes de cualquier piloto; reportar métricas por subgrupo.
- Recalibrar (Platt / *temperature scaling*) si se usa la probabilidad para priorizar.
- Mitigar atajos: recortar la región pulmonar o reentrenar con *augmentations* que eliminen marcadores.
- Considerar modelos multi-dataset (TorchXRayVision) como alternativa intercambiable vía `Classifier`.
