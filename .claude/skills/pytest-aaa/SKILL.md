---
name: pytest-aaa
description: Escribe y organiza pruebas pytest con patrón AAA para el proyecto Neumonía, usando los dobles existentes, las marcas model/slow y la compuerta de cobertura. Úsala siempre que agregues o cambies código.
---

# Pruebas con pytest (patrón AAA)

## Estructura de cada prueba
```python
def test_<comportamiento>_<condición>(fixtures):
    # Arrange: prepara datos y dobles
    # Act: UNA llamada al código bajo prueba
    # Assert: verifica el resultado observable (no detalles internos)
```
Usa `@pytest.mark.parametrize` para variantes en lugar de copiar pruebas.

## Dobles y fixtures disponibles (`tests/conftest.py`)
- `FakeClassifier(probs)` — probabilidades fijas, registra `calls`.
- `FakeExplainer` — mapa de calor fijo, registra `class_indices`.
- `ExplodingClassifier` — simula un error interno (→ 500).
- `fake_service`, `settings` (rutas en `tmp_path`), `png_bytes_sample`, `jpg_bytes_sample`,
  `dicom_bytes_sample`, `make_dicom_bytes(pixels, photometric, age, sex, view)`.
- `tiny_keras_model` — red mínima 512×512×1 → 3 con capa `conv10_thisone` (Keras real, rápida).
- `requires_model` — omite si no está `conv_MLP_84.h5`.

## Marcas
- `@pytest.mark.model` — usa el modelo real de 118 MB.
- `@pytest.mark.slow` — más de ~2 s.
`make test-fast` excluye ambas (ciclo rápido); CI las corre todas.

## Qué probar según la capa
| Capa | Qué verificar |
|---|---|
| readers | firma vs. extensión, DICOM MONOCHROME1/16 bits, corruptos → `InvalidImageError`, sin PHI |
| decision | tabla de casos límite del umbral |
| service | flujo con dobles, Grad-CAM sobre la clase decidida |
| api | 200 con muestras del aula, 422 parametrizado, 500 `{error}`, claves de `response_example.json` |
| arquitectura | `tests/test_architecture.py` (no se edita para "hacerla pasar") |

## Cerrar
`make check` → ruff + formato + pytest con `--cov-fail-under=80`. Nunca bajes el umbral para pasar.
