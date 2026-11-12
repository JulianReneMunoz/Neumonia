# Datos — Neumonía

| Fuente | Estado | Cómo obtenerla | Licencia |
|---|---|---|---|
| Aula: `JPG.zip` (12) + `DICOM.zip` (4) | ✅ local | `make data-course` | Uso académico |
| **RSNA Pneumonia 2018** (26 684 DICOM con edad, sexo y proyección) | ⬇️ descarga | `make dataset-rsna` (Kaggle) | Investigación/educación con atribución a RSNA |
| Kermany Chest X-Ray (5 856 JPG) | ⬇️ opcional | `make dataset-kermany` (Kaggle) | CC BY 4.0 |

- `data/raw/` — imágenes descargadas (no se versionan).
- `data/processed/<fuente>_metadata.csv` — catálogo con `target, subtype, rsna_class, n_boxes, age, age_group, sex, view_position, ...`.
- `data/processed/<fuente>_summary.json` — balance de clases y demografía (datasheet).

Justificación de la elección, datasheet y citas: [`docs/dataset.md`](../docs/dataset.md).

**Citas**
- Shih G. et al. (2019). *Augmenting the NIH Chest Radiograph Dataset with Expert Annotations of Possible Pneumonia*. Radiology: AI 1(1):e180041.
- Kermany D. et al. (2018). *Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning*. Cell 172(5):1122-1131. doi:10.17632/rscbjbr9sj.2
