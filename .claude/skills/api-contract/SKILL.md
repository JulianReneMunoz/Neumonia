---
name: api-contract
description: Modifica la API REST o gRPC del proyecto Neumonía sin romper el contrato del curso (label, probability, gradcam_url). Úsala al agregar campos, endpoints o códigos de error.
---

# Cambios de API sin romper el contrato

## Contrato estable
`POST /predict` → `label` (NORMAL|PNEUMONIA), `probability`, `gradcam_url`. Errores: `422` con
`detail[].loc/msg`, `500` con `{"error": "..."}`. No se devuelven rutas locales ni PHI.

## Tipos de cambio
- **Aditivo** (nuevo campo opcional, nuevo endpoint): permitido.
- **Incompatible** (renombrar/quitar campo, cambiar tipo o semántica): requiere `/v2` y un ADR.

## Pasos (en este orden)
1. `api/openapi.yaml` — actualiza el esquema y el ejemplo (contract-first).
2. `src/neumonia/api/schemas.py` — modelo Pydantic.
3. `src/neumonia/domain.py::Prediction.to_contract` si el dato viene del dominio.
4. `src/neumonia/api/app.py` — endpoint (siempre vía controlador).
5. gRPC: `grpc_api/neumonia.proto` → `make proto` → `grpc_api/server.py` (números de campo nuevos, nunca reutilizar).
6. Pruebas: `tests/test_api.py`, `tests/test_contract_and_config.py`, `tests/test_grpc.py`.
7. `api/README.md` y, si cambia el mínimo, `artifacts/expected/response_example.json`.
8. `make check` y `make docker-smoke` (si hay contenedor arriba).

## Verificación manual
```bash
make api
curl -s -F "file=@artifacts/samples/viral (3).dcm" localhost:8000/predict | python -m json.tool
```
