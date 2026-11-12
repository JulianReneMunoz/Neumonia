# FakeClassifier

> God node · 22 connections · `tests/conftest.py`

**Community:** [Community 10](Community_10.md)

## Connections by Relation

### calls
- test_evaluate_logs_metrics_and_artifacts() `EXTRACTED`
- test_gradcam_targets_decided_subtype() `EXTRACTED`
- test_explainer_factory_is_lazy() `EXTRACTED`
- test_gradcam_files_are_pruned() `EXTRACTED`
- test_evaluate_skips_missing_files() `EXTRACTED`
- fake_classifier() `EXTRACTED`
- test_without_explainer_heatmap_is_none() `EXTRACTED`

### contains
- conftest.py `EXTRACTED`

### imports
- test_evaluation_and_data.py `EXTRACTED`
- test_api.py `EXTRACTED`
- test_service.py `EXTRACTED`
- test_grpc.py `EXTRACTED`

### method
- .predict_proba() `EXTRACTED`
- .__init__() `EXTRACTED`

### rationale_for
- Devuelve siempre las mismas probabilidades y registra lo que recibe. `EXTRACTED`

### references
- 8. SOLID: patrón Estrategia e Inversión de Dependencias (DIP) `INFERRED`
- B. Ingeniería de software `INFERRED`
- Resultados (12/11/2026) `INFERRED`
- escritor-pruebas.md `INFERRED`
- Convenciones `INFERRED`

### uses
- client() `INFERRED`
- stub() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*