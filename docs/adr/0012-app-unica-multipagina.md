# ADR-0012 · Una sola aplicación para radiografía y tomografía

- **Estado**: aceptado (rama `feature/app-unica`) · **Fecha**: 2026-11-13

## Contexto
La radiografía (`make ui`, puerto 8501) y el prototipo de tomografía (`make ui-ct`, puerto 8502) eran dos
aplicaciones separadas. En la demo había que abrir dos direcciones y dos terminales.

## Decisión
1. **Nivel 1 (este ADR)**: una entrada multipágina de Streamlit, `view/app.py`, con `st.navigation`. Las páginas
   son las vistas existentes, **sin cambios**: «Radiografía» (`streamlit_app.py`, por defecto, `/radiografia`) y
   «Tomografía 3D (prototipo)» (`ct_app.py`, `/tomografia`). `make ui` y `make ui-seg` la abren en el puerto 8501.
2. `make ui-ct` se conserva como respaldo (solo tomografía, puerto 8502). Docker sigue sirviendo solo la radiografía.
3. La entrada no importa el modelo ni el controlador: solo apunta a las vistas (regla MVC de `test_architecture.py`).
4. **Nivel 2 (pendiente, M4)**: compartir el paciente entre páginas y un informe PDF único (radiografía +
   tomografía), con su historial y pruebas.

## Consecuencias
- (+) Una dirección y una terminal para toda la demo; se ve como un solo producto.
- (+) Riesgo bajo: las vistas no cambian y el respaldo de dos apps sigue disponible.
- (+) Sin choque TensorFlow/PyTorch: la página de tomografía solo lee casos precalculados (MEDPSeg corre aparte).
- (−) Aún no hay paciente ni informe compartidos (nivel 2).
- (−) La página de tomografía necesita el extra `ct` (ya incluido en `make install`).
