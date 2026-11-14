# Contrato de API — Neumonía

Implementación: `src/neumonia/api/app.py` (FastAPI). Especificación: [`openapi.yaml`](openapi.yaml).
Documentación interactiva con la API arriba: <http://localhost:8000/docs>.

## Endpoints

| Método | Ruta | Respuesta |
|---|---|---|
| `GET` | `/health` | `200 {status, model_loaded, model_version}` |
| `POST` | `/predict` | `200` contrato · `422` entrada inválida · `500 {"error": "..."}` |
| `GET` | `/static/gradcam/{id}.png` | PNG 512×512 con Grad-CAM |

gRPC equivalente (Clase 7): `src/neumonia/grpc_api/neumonia.proto`, puerto `50051` (`make grpc`).

## Entrada
`multipart/form-data` con el campo `file`: DICOM (`.dcm`), JPG o PNG, hasta 20 MB.
El formato se detecta por la **firma binaria** del archivo y, si no la hay, por la extensión.

## Salida
```json
{
  "label": "PNEUMONIA",
  "probability": 0.9921,
  "gradcam_url": "/static/gradcam/3f2b9c0e8a.png",
  "subtype": "viral",
  "class_probabilities": {"bacteriana": 0.1039, "normal": 0.0079, "viral": 0.8882},
  "metadata": {"age": 6, "sex": "F", "view_position": "AP", "modality": "CR", "body_part": "CHEST"},
  "model_version": "conv_MLP_84@modelo-v1",
  "request_id": "3f2b9c0e8a",
  "findings": {
    "zone_attention": {"derecho_superior": 0.217, "derecho_medio": 0.091, "derecho_inferior": 0.149,
                       "izquierdo_superior": 0.185, "izquierdo_medio": 0.097, "izquierdo_inferior": 0.221},
    "dominant_zone": "izquierdo_inferior",
    "laterality": "bilateral",
    "extent_pct": 4.0,
    "out_of_lung_pct": 42.0,
    "outside_inside_ratio": 1.04,
    "shortcut_warning": true,
    "attention_grid": [[0.0, "…31×31…"]],
    "summary": ["El modelo sugiere hallazgos compatibles con neumonía de probable patrón viral (probabilidad 99.2%).", "…"],
    "lung_source": "geometrica",
    "lung_note": "Segmentación pspnet descartada: un pulmón ocupa solo el 2 % de la imagen (…). Se usan zonas geométricas.",
    "lung_grid": [[0, "…64×64…"]]
  }
}
```

- `label` / `probability` / `gradcam_url`: contrato mínimo del curso (estable).
- `probability` es la probabilidad **de la etiqueta devuelta**: P(neumonía) = P(bacteriana) + P(viral)
  si `label = PNEUMONIA`, o P(normal) si `label = NORMAL` (ver ADR-0003).
- `subtype`, `class_probabilities`, `metadata`, `model_version`, `request_id`: campos aditivos.
- `findings` (v0.4.0, aditivo, puede ser `null`): informe de hallazgos asistido por zonas pulmonares
  aproximadas (ADR-0007, spec 005). `derecho`/`izquierdo` se refieren al **paciente** (convención radiológica).
  Describe la **atención del modelo**, no la ubicación de lesiones. `shortcut_warning = true` cuando el modelo
  mira tanto o más fuera de los pulmones que dentro.
- `findings.lung_source` / `lung_note` / `lung_grid` (v0.5.0, aditivos): si las zonas salen de la silueta
  segmentada con PSPNet (`NEUMONIA_LUNG_SEGMENTER=pspnet`, ADR-0008) o de rectángulos geométricos, por qué
  se usó el respaldo, y la máscara 64×64 para dibujarla.

## Reglas
- `Content-Type: application/json` en todas las respuestas JSON.
- Validación: `422` con `detail[].loc` y `detail[].msg`.
- Errores del modelo: `500` con `{"error": "..."}`, sin trazas internas.
- No se devuelven rutas locales ni identificadores del paciente (PatientID/PatientName se descartan).
- El contrato es estable aunque cambie el modelo; los cambios incompatibles requieren `/v2`.

## Ejemplos
```bash
curl -s localhost:8000/health
curl -s -F "file=@artifacts/samples/viral (3).dcm" localhost:8000/predict
```
```powershell
curl.exe -s -F "file=@artifacts/samples/person1711_bacteria_4527.jpeg" http://localhost:8000/predict
```
