# Spec 005 · Informe de hallazgos asistido y vistas 3D

Historia **HU-08**: *Como médico quiero un informe detallado de en qué zonas del pulmón se basó el modelo y
verlo en 3D, para revisar la sugerencia con rapidez sin confundirla con una lectura radiológica.*
Decisión: [ADR-0007](../docs/adr/0007-hallazgos-por-zonas-y-vista-3d.md).

| # | Criterio de aceptación | Prueba (`tests/test_hallazgos_3d.py`) |
|---|---|---|
| 1 | Seis zonas disjuntas dentro de la imagen; el mediastino y los bordes quedan fuera del campo pulmonar | `test_zone_masks_are_six_disjoint_regions_inside_the_image`, `test_lung_field_is_union_of_zones_and_excludes_borders` |
| 2 | Convención radiológica: atención en la izquierda de la imagen → pulmón **derecho** del paciente | `test_attention_on_image_left_lower_is_patient_right_lower` |
| 3 | Lateralidad derecho / izquierdo / bilateral / sin foco | `test_classify_laterality` |
| 4 | Atención concentrada fuera de los pulmones → alerta de atajo con razón finita | `test_attention_outside_lungs_triggers_shortcut_warning` |
| 5 | Atención uniforme → razón ≈ 1.0 (referencia de la alerta) | `test_uniform_attention_has_density_ratio_close_to_one` |
| 6 | Mapa vacío o NaN → sin foco, sin alerta, sin división por cero | `test_empty_or_nan_attention_has_no_focus_and_no_warning` |
| 7 | El informe usa lenguaje de sugerencia, nombra la zona y termina con la nota de limitación | `test_describe_pneumonia_mentions_subtype_zone_and_note`, `test_describe_normal_and_shortcut_warning`, `test_describe_diffuse_attention_has_no_grammar_glitch` |
| 8 | `findings` es aditivo en `/predict`; los campos del contrato mínimo no cambian | `test_api_predict_includes_findings` |
| 9 | Sin explicador (evaluación masiva) → `findings = null` | `test_service_without_explainer_has_no_findings` |
| 10 | La pasarela HTTP reconstruye `Findings` desde el JSON (ida y vuelta) | `test_http_gateway_parses_findings`, `test_findings_roundtrip_dict` |
| 11 | El PDF incluye la sección de hallazgos | `test_pdf_report_with_findings_is_valid_and_larger` |
| 12 | Vista 3D: relieve (2 superficies) y esquema de dos pulmones con 6 rótulos; entradas inválidas → `ValueError` | `test_attention_surface_figure_*`, `test_lungs_3d_figure_*` |
| 13 | La vista no importa `neumonia.model` ni TensorFlow (capas MVC) | `test_architecture.py` |

**Fuera de alcance**: segmentar lesiones, reconstruir anatomía 3D, emitir un diagnóstico.
