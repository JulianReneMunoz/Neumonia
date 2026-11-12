# ADR-0002 · Reutilizar conv_MLP_84 y descargarlo verificado

- **Estado**: aceptado · **Fecha**: 2026-10-24

## Contexto
El curso evalúa el contrato y el despliegue, no la métrica. El `.h5` pesa 118 MB (GitHub rechaza >100 MB) y no
debe versionarse. Hugging Face y otros hubs ofrecen modelos de 2 clases con licencias heterogéneas.

## Decisión
Usar el modelo del caso base, publicado en el Release público `modelo-v1`, descargándolo con
`scripts/fetch_model.py`: URL https, archivo temporal `.part` y verificación SHA-256 antes de aceptarlo.
La versión expuesta en la API es `conv_MLP_84@modelo-v1`.

## Consecuencias
- (+) Resultados comparables con los demás equipos; integridad verificable (cadena de suministro).
- (+) CI cachea el archivo por hash; Docker lo descarga en la etapa de *build*.
- (−) Dependencia de un Release externo → mitigación: espejo en el registro de imágenes (R-06).
- (−) Modelo entrenado en pediatría → riesgo R-02, documentado en la Model Card.
