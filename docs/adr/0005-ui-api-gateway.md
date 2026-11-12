# ADR-0005 · Streamlit clínico + FastAPI + gRPC con pasarela intercambiable

- **Estado**: aceptado · **Fecha**: 2026-11-07

## Contexto
El taller pide "Streamlit clínico" para Neumonía; el M3 pide backend/API (FastAPI/gRPC); el M4 pide un sistema
desplegado (producto, no notebook). El monolito usaba Tkinter con capturas de pantalla (`tkcap`), que no funcionan
en un servidor.

## Decisión
- Vista: Streamlit. El PDF se genera desde los datos con `fpdf2`, no desde capturas.
- La vista habla con una `PredictionGateway`: `LocalGateway` (mismo proceso) o `HttpGateway` (API), elegida por
  `NEUMONIA_API_URL`. En Docker Compose la UI usa la API y no carga el modelo.
- API REST (FastAPI) como interfaz pública; gRPC para clientes internos.

## Consecuencias
- (+) Un solo modo de desarrollo (`make ui`) y un despliegue cliente-servidor sin cambiar la vista.
- (+) UI y API escalan por separado.
- (−) Tkinter queda fuera (el curso acepta Streamlit o Tkinter).
