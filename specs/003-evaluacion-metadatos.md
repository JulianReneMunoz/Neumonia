# Spec 003 · Evaluación con metadatos

| # | Criterio de aceptación | Prueba / evidencia |
|---|---|---|
| 1 | El catálogo incluye edad, grupo etario, sexo y proyección sin identificadores | `test_evaluation_and_data.py::test_load_rsna_merges_labels_classes_and_headers` |
| 2 | Submuestra estratificada y reproducible por semilla | `test_stratified_subset_*` |
| 3 | Métricas: exactitud, precisión, sensibilidad, especificidad, F1, AUC | `test_binary_metrics_*`, `test_roc_auc_known_values` |
| 4 | Sensibilidad por sexo, edad y proyección registrada en MLflow | `test_evaluate_logs_metrics_and_artifacts` |
| 5 | Corrida RSNA (500) registrada y copiada a la Model Card | ⬜ `run_id` pendiente |
