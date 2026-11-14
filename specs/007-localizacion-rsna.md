# Spec 007 · ¿Grad-CAM apunta a la lesión? (fase 2 de la localización)

Historia **HU-10**: *Como equipo queremos medir, contra las cajas de los radiólogos de RSNA, cuánto
coincide la atención del modelo con la lesión, para reportar una cifra honesta en la Model Card.*
Decisión: [ADR-0009](../docs/adr/0009-metricas-localizacion-gradcam.md).

| # | Criterio de aceptación | Prueba (`tests/test_localizacion_rsna.py`) |
|---|---|---|
| 1 | Lee las cajas de Kaggle (`stage_2_train_labels.csv`, patientId) o de la exportación adjudicada (`rsna_boxes.csv`, SOPInstanceUID), ignorando negativos; formato desconocido → error claro | `test_load_rsna_boxes_groups_by_patient_and_ignores_negatives`, `test_load_boxes_from_adjudicated_export_keyed_by_sop_uid`, `test_load_boxes_rejects_unknown_format` |
| 2 | Solo casos con DICOM disponible (busca en subcarpetas); muestreo reproducible con semilla y límite | `test_build_cases_requires_image_and_is_reproducible` |
| 3 | Cajas reescaladas a 512×512 y recortadas al borde | `test_boxes_mask_rescales_from_original_resolution`, `test_boxes_mask_clips_boxes_outside_the_image` |
| 4 | Atención sobre la lesión → acierto, enriquecimiento > 1, IoU alto | `test_attention_on_the_lesion_scores_high` |
| 5 | Atención en un marcador → fallo y enriquecimiento < 1 | `test_attention_on_a_marker_scores_below_chance` |
| 6 | Atención uniforme → enriquecimiento ≈ 1 (azar) | `test_uniform_attention_equals_chance` |
| 7 | Mapa vacío → ceros sin dividir por cero | `test_empty_attention_scores_zero_without_dividing_by_zero` |
| 8 | IC 95 % de Wilson correcto | `test_wilson_interval_known_values` |
| 9 | Resumen global y del subconjunto clasificado como neumonía | `test_summarize_reports_global_and_true_positive_subset` |
| 10 | Extremo a extremo: omite archivos corruptos, escribe CSV/JSON, registra en MLflow, sin PHI | `test_evaluate_localization_writes_results_and_logs_metrics` |

**Pendiente**: correr `make evaluate-loc` con RSNA (300 casos) y anotar el `run_id` y las cifras en la Model Card.
