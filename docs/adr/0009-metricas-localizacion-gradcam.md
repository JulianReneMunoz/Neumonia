# ADR-0009 · Medir si Grad-CAM apunta a la lesión con las cajas de RSNA

- **Estado**: propuesto (rama `feature/localizacion-rsna`) · **Fecha**: 2026-11-12

## Contexto
El informe (ADR-0007) y la segmentación (ADR-0008) describen **dónde miró el modelo**, pero no
sabemos si eso coincide con la lesión. Hasta ahora la evidencia es cualitativa (un caso,
`viral (3).dcm`, con atención en el marcador). RSNA 2018 trae, para cada radiografía con neumonía,
de 1 a 4 cajas de opacidad dibujadas por radiólogos (`stage_2_train_labels.csv`): un patrón de
referencia gratuito para medirlo.

## Decisión
Evaluar el Grad-CAM de la clase decidida contra la **unión de las cajas**, en la misma geometría que
ve el modelo (512×512; la imagen se redimensiona sin recorte, así que las cajas solo se escalan),
con tres métricas habituales para mapas de saliencia y su **línea base de azar**:

| Métrica | Pregunta | Línea base |
|---|---|---|
| Acierto del máximo (*pointing game*) | ¿la región de máxima atención cae dentro de una caja? | fracción del área cubierta por cajas |
| Energía dentro / enriquecimiento | ¿qué fracción de la atención cae en las cajas? ¿cuántas veces más que el azar? | enriquecimiento = 1.0 |
| IoU | ¿cuánto se solapa la región de alta atención (≥ 0.5) con las cajas? | — |

- Se reporta para todos los casos con cajas y, aparte, para los que el modelo clasificó como
  neumonía (`tp_*`), porque en un falso negativo Grad-CAM explica la clase "normal".
- IC 95 % de Wilson para la tasa de acierto. 300 casos por defecto (`make evaluate-loc`), con semilla.
- Todo se registra en MLflow (experimento de localización) con un CSV por caso.
- La región del máximo usa los píxeles ≥ 99 % del máximo (robusta a empates en mapas planos).

## Alternativas descartadas
- **Solo inspección visual**: no escala ni da una cifra para la Model Card.
- **Métricas de segmentación (Dice) contra máscaras de lesión**: RSNA no trae máscaras, solo cajas.
- **Evaluar con el dataset del aula**: sus DICOM no traen cajas.

## Consecuencias
- (+) Una cifra honesta y reproducible: "Grad-CAM apunta a la lesión en X % de los casos (IC …)".
- (+) Cuantifica el riesgo de atajos R-05 a escala, no solo en un caso.
- (−) Las cajas son rectángulos generosos: el IoU queda bajo incluso con buena atención; por eso el
  enriquecimiento y el *pointing game* son las métricas principales.
- (−) Grad-CAM es de baja resolución (31×31): limita el IoU máximo alcanzable.
