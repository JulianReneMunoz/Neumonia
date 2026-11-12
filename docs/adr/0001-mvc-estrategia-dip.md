# ADR-0001 · Arquitectura MVC con Estrategia e inversión de dependencias

- **Estado**: aceptado · **Fecha**: 2026-10-24

## Contexto
El monolito `detector_neumonia.py` (251 líneas) mezclaba Tkinter, TensorFlow 1 (`K.gradients`), lectura DICOM y CSV.
No se podía probar sin interfaz gráfica ni desplegar en un servidor. La DoD del M1 exige MVC, y la Clase 1 pide
cohesión alta, acoplamiento bajo y los patrones Estrategia + DIP.

## Decisión
Paquete `src/neumonia` con capas `model/`, `controller/` y `view/`, más adaptadores `api/` y `grpc_api/`.
Puntos de variación como `Protocol`: `ImageReader`, `Classifier`, `Explainer`, `DecisionPolicy`,
`PredictionGateway` y `Tracker`. Una sola raíz de composición: `controller/factory.py`.

## Consecuencias
- (+) Las pruebas del controlador y de la API corren sin TensorFlow (dobles), en segundos.
- (+) Tres interfaces (Streamlit, REST, gRPC) comparten un único controlador.
- (+) Reglas verificadas en CI (`tests/test_architecture.py`).
- (−) Más archivos que el monolito; se compensa con `CLAUDE.md` y la skill `mvc-feature`.
