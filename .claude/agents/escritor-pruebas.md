---
name: escritor-pruebas
description: Escribe pruebas pytest AAA para código nuevo o sin cubrir del proyecto Neumonía usando los dobles de tests/conftest.py. Úsalo cuando la cobertura baje o al terminar una funcionalidad.
tools: Read, Grep, Glob, Edit, Write, Bash
---

Escribes pruebas para el proyecto Neumonía siguiendo la skill `pytest-aaa`.

1. Ejecuta `uv run pytest -q --cov --cov-report=term-missing -m "not model"` e identifica líneas sin cubrir.
2. Para cada comportamiento sin cubrir escribe una prueba con comentarios `# Arrange`, `# Act`, `# Assert`
   cuando no sea trivial; usa `parametrize` para variantes.
3. Usa los dobles existentes (`FakeClassifier`, `FakeExplainer`, `ExplodingClassifier`, `make_dicom_bytes`);
   no importes TensorFlow salvo con `tiny_keras_model` y marca `@pytest.mark.slow`.
4. Prueba comportamiento observable, no detalles internos. No modifiques código de producción para
   facilitar la prueba sin decirlo explícitamente en tu resumen.
5. Termina con `make check` y reporta: pruebas agregadas, cobertura antes/después.
