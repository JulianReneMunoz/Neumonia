# InvalidImageError

> God node · 26 connections · `src/neumonia/model/readers.py`

**Community:** [Community 3](Community_3.md)

## Connections by Relation

### calls
- select_reader() `EXTRACTED`
- to_uint8() `EXTRACTED`
- to_three_channels() `EXTRACTED`
- .read() `EXTRACTED`
- .read() `EXTRACTED`

### contains
- readers.py `EXTRACTED`

### imports
- evaluation.py `EXTRACTED`
- app.py `EXTRACTED`
- server.py `EXTRACTED`
- errors.py `EXTRACTED`

### inherits
- ValueError `EXTRACTED`

### rationale_for
- La entrada no es una radiografía legible (vacía, corrupta o formato no… `EXTRACTED`

### references
- Resultados (12/11/2026) `INFERRED`
- 2.1 Requisitos funcionales clave `INFERRED`
- Qué probar según la capa `INFERRED`

### uses
- [evaluate()](evaluate.md) `INFERRED`
- [create_app()](create_app.md) `INFERRED`
- PneumoniaDetectorServicer `INFERRED`
- test_black_image_is_rejected() `INFERRED`
- test_select_reader_rejects_unknown_formats() `INFERRED`
- test_to_three_channels_rejects_odd_shapes() `INFERRED`
- test_to_uint8_rejects_nan() `INFERRED`
- test_dicom_reader_rejects_garbage() `INFERRED`
- test_raster_reader_rejects_corrupt_png() `INFERRED`
- test_select_reader_rejects_empty_bytes() `INFERRED`
- test_invalid_bytes_raise() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*