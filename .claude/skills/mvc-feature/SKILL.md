---
name: mvc-feature
description: Implementa una funcionalidad nueva en el proyecto Neumonía respetando MVC, Estrategia e inversión de dependencias. Úsala al agregar un formato de imagen, un modelo, una regla de decisión, un campo de la UI o un endpoint.
---

# Implementar una funcionalidad respetando MVC

## 1. Ubica la capa correcta
| Si el cambio es… | Va en… | Patrón |
|---|---|---|
| Leer un formato nuevo (NIfTI, TIFF) | `model/readers.py` → nueva clase con `extensions`, `can_read`, `read` y agregarla a `DEFAULT_READERS` | Estrategia |
| Cambiar de modelo (ONNX, PyTorch) | `model/` nueva clase que cumpla `Classifier` + registrarla en `controller/factory.py` | DIP |
| Nueva regla de negocio (umbral, triage) | `controller/decision.py` → clase con `decide(probs) -> Decision` | Estrategia |
| Orquestación (nuevo paso del flujo) | `controller/service.py` (recibe dependencias por constructor) | DIP |
| Algo que se muestra | lógica en `view/presenter.py` (probable), widgets en `view/streamlit_app.py` | Humble Object |
| Exponerlo por red | `api/app.py` o `grpc_api/server.py`, siempre llamando al controlador | Adaptador |

## 2. Reglas que no se negocian
- La vista no importa `neumonia.model`, TensorFlow ni OpenCV. Si necesita un error, re-expórtalo en `controller/errors.py`.
- Solo `controller/factory.py` crea objetos concretos.
- TensorFlow se importa dentro de funciones.
- No se toca `model/preprocessing.py` (paridad con el entrenamiento).

## 3. Flujo
1. Escribe primero la prueba (skill `pytest-aaa`) con un doble de `tests/conftest.py`.
2. Implementa la clase/función mínima.
3. Si afecta la API, sigue la skill `api-contract`.
4. `make check`. Si `tests/test_architecture.py` falla, moviste algo a la capa equivocada.
5. Si es una decisión de arquitectura, agrega un ADR en `docs/adr/` (plantilla: contexto, decisión, consecuencias).

## Ejemplo: nuevo lector
```python
class TiffReader:
    extensions = (".tif", ".tiff")

    def can_read(self, data: bytes) -> bool:
        return data[:4] in (b"II*\x00", b"MM\x00*")

    def read(self, data: bytes) -> RadiographImage: ...
```
Prueba: `select_reader("x.tif", data)` devuelve `TiffReader` y `read_image` produce `uint8 (H, W, 3)`.
