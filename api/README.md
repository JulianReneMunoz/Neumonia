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
  "request_id": "3f2b9c0e8a"
}
```

- `label` / `probability` / `gradcam_url`: contrato mínimo del curso (estable).
- `probability` es la probabilidad **de la etiqueta devuelta**: P(neumonía) = P(bacteriana) + P(viral)
  si `label = PNEUMONIA`, o P(normal) si `label = NORMAL` (ver ADR-0003).
- `subtype`, `class_probabilities`, `metadata`, `model_version`, `request_id`: campos aditivos.

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
