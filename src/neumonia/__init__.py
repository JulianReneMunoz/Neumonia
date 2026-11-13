"""Neumonía — apoyo al diagnóstico de neumonía con Keras/TF y Grad-CAM (arquitectura MVC).

Capas:
- `neumonia.model`      → Modelo: lectura de imágenes, preprocesamiento, red neuronal, Grad-CAM.
- `neumonia.controller` → Controlador: orquesta el flujo y aplica las reglas de negocio.
- `neumonia.view`       → Vista: interfaz clínica en Streamlit.
- `neumonia.api` / `neumonia.grpc_api` → Adaptadores de entrega (REST y gRPC).
"""

__version__ = "0.4.0"
