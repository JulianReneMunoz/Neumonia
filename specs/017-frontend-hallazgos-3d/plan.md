# Plan · SPEC-017
- Solo frontend: `index.html` (pestañas y contenedores), `app.js` (render del informe y superficie 3D en
  canvas 2D con proyección y algoritmo del pintor), `styles.css`.
- Decisión: canvas propio en lugar de Plotly.js para no depender de una CDN en el salón ni agregar 3.5 MB.
- Riesgo: la vista 3D puede interpretarse como anatomía → texto fijo que lo aclara.
- Pruebas: prueba estática de pytest + E2E con Playwright (DICOM, JPG y respuesta sin `findings`).
