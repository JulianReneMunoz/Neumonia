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
| RSNA subconjunto estratificado (12/11/2026) | 500 | 0.63 | 0.74 (IC 95 % 0.66–0.81) | 0.59 (IC 95 % 0.54–0.64) | 0.73 | 120 opacidad / 165 normal / 215 otra anormalidad; `run_id` `e38783032379417fa23eec3491788318` |

Se reportan además, en MLflow, la sensibilidad por `sex`, `age_group` y `view_position`.

### Clasificación en RSNA por subgrupo (corrida del 12/11/2026)
500 radiografías de la exportación adjudicada de RSNA (semilla 42; 471 de adultos y 29 de menores de 18 años),
umbral 0.5, sin cambios en el código. Positivo = `Lung Opacity`; negativo = `Normal` o
`No Lung Opacity / Not Normal` (otra anormalidad sin neumonía), que se reportan también por separado.

| Comparación | n | Sensibilidad | Especificidad (IC 95 %) | AUC |
|---|---|---|---|---|
| Opacidad vs. todo lo demás | 500 | 0.74 | 0.59 (0.54–0.64) | 0.73 |
| Opacidad vs. Normal | 285 | 0.74 | 0.73 (0.66–0.80) | 0.82 |
| Opacidad vs. otra anormalidad | 335 | 0.74 | 0.48 (0.41–0.55) | 0.66 |

| Variable | Grupo | n | Sensibilidad | Especificidad | AUC |
|---|---|---|---|---|---|
| Sexo | F | 227 | 0.72 | 0.61 | 0.72 |
| Sexo | M | 273 | 0.76 | 0.58 | 0.73 |
| Edad | 0–17 | 29 | 0.92 | 0.44 | 0.82 |
| Edad | 18–39 | 140 | 0.77 | 0.63 | 0.77 |
| Edad | 40–64 | 265 | 0.66 | 0.59 | 0.67 |
| Edad | 65+ | 66 | 0.81 | 0.56 | 0.75 |
| Proyección | AP | 229 | 0.89 | 0.19 | 0.60 |
| Proyección | PA | 271 | 0.30 | 0.82 | 0.61 |

**Lectura.**
1. **La proyección decide más que el pulmón.** En AP el modelo dice "neumonía" casi siempre (especificidad 0.19);
   en PA casi nunca (sensibilidad 0.30). Dentro de cada proyección el AUC cae a ≈ 0.60, por debajo del global
   (0.73): buena parte de la discriminación global viene de separar AP de PA, no de la lesión. En RSNA las placas
   AP son portátiles, de pacientes más enfermos, y concentran los positivos. Es el aprendizaje por atajos (R-05)
   que ya mostraban Grad-CAM (2.7 % de acierto del máximo) y la alerta de atajo (83 %).
2. **Detecta "anormal", no "neumonía".** Contra radiografías normales el AUC es 0.82, pero contra otras
   anormalidades baja a 0.66 y la especificidad a 0.48.
3. **Sexo**: sin diferencia relevante (AUC 0.72 vs. 0.73). **Edad**: el peor grupo es 40–64 (AUC 0.67); el grupo
   0–17 tiene solo 29 casos y no permite conclusiones.

Con estas cifras el modelo no es apto para uso clínico en adultos; sirve como demostración educativa de cómo se
detecta y documenta el riesgo. Cualquier modelo que lo reemplace debería reportar el AUC **por proyección** como
criterio de aceptación.
Latencia medida en CPU (2 vCPU): ≈ 0.5 s de inferencia + ≈ 0.5 s de Grad-CAM por imagen; carga inicial ≈ 1 s.

### ¿Grad-CAM apunta a la lesión? (ADR-0009, spec 007)
Contra las cajas de opacidad de los radiólogos de RSNA, en la geometría que ve el modelo (512×512).

Corrida del 12/11/2026: 300 radiografías de RSNA con opacidad marcada (exportación adjudicada, semilla 42),
umbral 0.5, zonas geométricas. Registrada en MLflow (experimento de localización; `run_id`: b39b72dd2a414bd194a3802d4ecf30c8).

| Métrica | Todos los casos con cajas (n = 300) | Clasificados como neumonía (n = 215) | Línea base (azar) |
|---|---|---|---|
| Acierto del máximo (*pointing game*) | 2.7 % (IC 95 % 1.4–5.2 %) | 3.3 % (IC 95 % 1.6–6.6 %) | 11.7 % / 12.9 % (área en cajas) |
| Enriquecimiento (energía dentro / área) | 0.73 | 0.73 | 1.0 |
| IoU región de alta atención vs. cajas | 0.007 | 0.010 | — |
| Casos con alerta de atajo | 83 % (IC 95 % 78–87 %) | 80 % | — |

**Conclusión: en adultos (RSNA), Grad-CAM de `conv_MLP_84` no apunta a la lesión; lo hace peor que el azar.**
La atención cae menos dentro de las cajas de los radiólogos de lo que caería al azar (enriquecimiento 0.73),
y la alerta de atajo se activa en 83 % de los casos, lo que confirma que la alerta marca justo cuándo la
explicación no es confiable. Causas probables: cambio de dominio (entrenado con radiografías pediátricas de
Kermany) y aprendizaje por atajos (R-05). Además, el modelo clasificó como neumonía 215 de los 300 casos con
opacidad (sensibilidad 71.7 %, IC 95 % 66.3–76.5 %) en este subconjunto. Con estas cifras, el mapa de calor
no debe presentarse como localización de la lesión.

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
2. **Sesgo medido por proyección**: en RSNA la especificidad es 0.19 en AP y la sensibilidad 0.30 en PA (ver
   Métricas); por sexo no se observó diferencia relevante.
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
- Validación en RSNA hecha (AUC 0.73, sesgo por proyección); falta validar en datos locales antes de cualquier
  piloto y exigir AUC por proyección ≥ al global.
- Recalibrar (Platt / *temperature scaling*) si se usa la probabilidad para priorizar.
- Mitigar atajos: recortar la región pulmonar o reentrenar con *augmentations* que eliminen marcadores.
- Considerar modelos multi-dataset (TorchXRayVision) como alternativa intercambiable vía `Classifier`.
