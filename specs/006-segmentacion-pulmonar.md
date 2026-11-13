# Spec 006 · Segmentación pulmonar real (fase 1 de la localización)

Historia **HU-09**: *Como médico quiero que las zonas del informe sigan la forma real de los pulmones
del paciente, y saber cuándo no fue posible segmentarlos, para confiar en la lateralidad, la extensión
y la alerta de atajo.* Decisión: [ADR-0008](../docs/adr/0008-segmentacion-pulmonar-pspnet.md).

| # | Criterio de aceptación | Prueba (`tests/test_segmentacion_pulmonar.py`) |
|---|---|---|
| 1 | Por defecto (sin configurar) el comportamiento es idéntico a la versión 0.4.0 | `test_geometric_segmenter_matches_previous_zones`, suite de spec 005 |
| 2 | "Right Lung" de PSPNet = pulmón derecho del paciente (izquierda de la imagen); la entrada usa la escala de TorchXRayVision | `test_xrv_segmenter_maps_anatomic_names_and_normalizes_input` |
| 3 | La máscara conserva el componente mayor y rellena huecos | `test_clean_mask_*` |
| 4 | Control de calidad: rechaza pulmón diminuto, área total baja, lados invertidos o superposición | `test_quality_rejects_implausible_masks` (4 casos), `test_quality_accepts_anatomic_lungs` |
| 5 | Si PSPNet falla o no es plausible → zonas geométricas + nota explicativa en el informe | `test_quality_checked_falls_back_*`, `test_describe_mentions_segmentation_source_or_fallback_note` |
| 6 | PyTorch corre en un proceso hijo; los errores llegan al padre y el hijo se recrea si muere | `test_isolated_segmenter_*`, `test_worker_*` |
| 7 | Zonas en tercios de la altura de cada pulmón, disjuntas y que cubren el pulmón | `test_zones_follow_each_lung_own_height` |
| 8 | `findings` incluye `lung_source`, `lung_note` y `lung_grid` (64×64) | `test_findings_roundtrip_keeps_segmentation_fields`, `test_analyze_attention_uses_given_lungs` |
| 9 | La vista dibuja los pulmones, sus tercios y la zona dominante (solo numpy) | `test_zones_overlay_*`, `test_present_findings_shows_segmentation_source` |
| 10 | Configurable con `NEUMONIA_LUNG_SEGMENTER` (`geometrica` \| `pspnet`); valores inválidos se rechazan | `test_settings_reads_segmenter_from_env`, `test_build_segmenter_from_settings` |
| 11 | Pesos verificados con SHA-256 | `test_verify_weights_detects_tampering` |
| 12 | PyTorch/TorchXRayVision solo se importan de forma perezosa y nunca en vista ni controlador | `test_architecture.py` |
| 13 | Con PSPNet real, una muestra del curso se segmenta y supera el control de calidad | `test_real_pspnet_segments_course_sample` (marca `model`, requiere `make seg`) |

**Fuera de alcance**: localizar lesiones (fase 3), medir Grad-CAM contra las cajas de RSNA (fase 2).
