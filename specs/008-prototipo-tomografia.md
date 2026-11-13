# Spec 008 · Prototipo de tomografía con reconstrucción 3D de la lesión

Historia **HU-11**: *Como médico quiero ver en 3D los pulmones, la vía aérea, las arterias y la lesión
de una tomografía, con el porcentaje comprometido por lóbulo, para dimensionar la extensión de la
neumonía.* Decisión: [ADR-0010](../docs/adr/0010-prototipo-tomografia-medpseg.md). Estado: prototipo.

| # | Criterio de aceptación | Prueba (`tests/test_tomografia.py`) |
|---|---|---|
| 1 | Lee las salidas de MEDPSeg y las reorienta a RAS+ (derecho del paciente = x alto), incluidos los lóbulos con metadatos inconsistentes | `test_load_medpseg_output_reorients_to_ras` |
| 2 | Tolera salidas opcionales ausentes; sin pulmones → error claro | `test_load_medpseg_output_tolerates_missing_optional_files`, `test_load_medpseg_output_requires_lungs` |
| 3 | MEDPSeg corre como proceso externo con el script propio y el remuestreo indicado; fallos y entorno ausente → errores claros | `test_medpseg_segmenter_*` |
| 4 | Puntaje de severidad por lóbulo en las bandas 0/<5/5–25/26–50/51–75/>75 %, con umbral de ruido del 1 % | `test_lobe_severity_bands` (10 casos), `test_minimal_findings_are_reported_as_noise` |
| 5 | Volúmenes y % por pulmón y lóbulo; lóbulo más comprometido; nota de prototipo | `test_analyze_quantifies_lesion_by_lung_and_lobe`, `test_analyze_without_lesion_or_lobes`, `test_describe_bilateral` |
| 6 | Mallas en milímetros; caché de pocos MB que carga sin MEDPSeg | `test_downsample_and_mesh_are_in_millimetres`, `test_cache_roundtrip_and_version`, `test_service_caches_and_loads_cases` |
| 7 | Vista 3D anterior con estructuras seleccionables y rótulos de lado correctos | `test_figure_3d_respects_visible_structures_and_labels_sides` |
| 8 | Cortes axial y coronal con el derecho del paciente a la izquierda y la lesión superpuesta | `test_slice_image_shows_right_lung_on_screen_left` (2 planos) |
| 9 | La vista no importa `neumonia.model` (MVC) | `test_architecture.py` |

**Pendiente**: validar contra las 20 CT de COVID-19-CT-Seg (Dice de lesión) y medir tiempos en el equipo de la demo.
