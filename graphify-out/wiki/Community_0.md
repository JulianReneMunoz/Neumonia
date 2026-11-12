# Community 0

> 20 nodes

## Key Concepts

- **preprocess()** (12 connections) — `src/neumonia/model/preprocessing.py`
- **test_preprocessing.py** (12 connections) — `tests/test_preprocessing.py`
- **cv2** (11 connections)
- **preprocessing.py** (10 connections) — `src/neumonia/model/preprocessing.py`
- **to_gray()** (6 connections) — `src/neumonia/model/preprocessing.py`
- **apply_clahe()** (5 connections) — `src/neumonia/model/preprocessing.py`
- **resize_for_display()** (4 connections) — `src/neumonia/model/preprocessing.py`
- **test_preprocess_rejects_float_input()** (4 connections) — `tests/test_preprocessing.py`
- **test_to_gray_rejects_4_channels()** (4 connections) — `tests/test_preprocessing.py`
- **ndarray** (4 connections)
- **test_clahe_increases_local_contrast()** (3 connections) — `tests/test_preprocessing.py`
- **test_preprocess_custom_size()** (3 connections) — `tests/test_preprocessing.py`
- **test_preprocess_output_shape_and_range()** (3 connections) — `tests/test_preprocessing.py`
- **test_resize_for_display()** (3 connections) — `tests/test_preprocessing.py`
- **test_to_gray_accepts_2d_and_3_channels()** (3 connections) — `tests/test_preprocessing.py`
- **test_preprocess_is_deterministic()** (2 connections) — `tests/test_preprocessing.py`
- **parametrize** (1 connections)
- **Preprocesamiento idéntico al del entrenamiento de conv_MLP_84. 512×512 → escala…** (1 connections) — `src/neumonia/model/preprocessing.py`
- **Devuelve el tensor listo para el modelo: float32 (1, size, size, 1) en [0, 1].** (1 connections) — `src/neumonia/model/preprocessing.py`
- **Preprocesamiento: paridad con el entrenamiento (512×512, gris, CLAHE, [0,1]).** (1 connections) — `tests/test_preprocessing.py`

## Relationships

- [Community 15](Community_15.md) (8 shared connections)
- [Community 3](Community_3.md) (5 shared connections)
- [Community 18](Community_18.md) (3 shared connections)
- [Community 37](Community_37.md) (2 shared connections)
- [Community 14](Community_14.md) (2 shared connections)
- [Community 59](Community_59.md) (1 shared connections)

## Source Files

- `src/neumonia/model/preprocessing.py`
- `tests/test_preprocessing.py`

## Audit Trail

- EXTRACTED: 57 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*