# Spec 002 · Explicabilidad Grad-CAM

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | El mapa es RGB uint8 512×512 superpuesto con JET (α = 0.8) | `test_service.py::test_heatmap_is_rgb_512` |
| 2 | Se explica la clase de la decisión, no siempre el argmax | `test_service.py::test_gradcam_targets_decided_subtype` |
| 3 | Mapa degenerado (todo ≤ 0 o NaN) → ceros, sin división por cero | `test_gradcam_and_classifier.py::test_normalize_heatmap_degenerate_returns_zeros` |
| 4 | Funciona con un modelo Keras real (`tf.GradientTape`, todos los filtros) | `test_gradcam_and_classifier.py::test_gradcam_explainer_with_tiny_model` |
| 5 | Con el modelo real, el mapa no es constante | `test_real_model.py::test_gradcam_is_not_constant` |
| 6 | `explain=False` omite el cálculo (evaluaciones masivas) | `test_service.py::test_explain_false_skips_gradcam` |
