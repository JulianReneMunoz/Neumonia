"""Reglas de arquitectura MVC verificadas automáticamente (fitness functions).

Si alguien hace que la vista importe el modelo, o que el modelo importe la API, la
prueba falla en CI: la arquitectura no depende de la disciplina, sino de una compuerta.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "neumonia"

FORBIDDEN = {
    "model": (
        "neumonia.controller",
        "neumonia.view",
        "neumonia.api",
        "neumonia.grpc_api",
        "streamlit",
        "fastapi",
    ),
    "view": ("neumonia.model", "tensorflow", "cv2", "fastapi"),
    "controller": ("neumonia.view", "neumonia.api", "neumonia.grpc_api", "streamlit", "fastapi"),
    "api": ("neumonia.view", "streamlit"),
    "grpc_api": ("neumonia.view", "streamlit", "fastapi"),
}


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


CASES = [(layer, path) for layer in FORBIDDEN for path in sorted((SRC / layer).glob("*.py"))]


@pytest.mark.parametrize(("layer", "path"), CASES, ids=[f"{lay}/{p.name}" for lay, p in CASES])
def test_layer_does_not_import_forbidden_modules(layer, path):
    bad = {imp for imp in imports_of(path) for prefix in FORBIDDEN[layer] if imp.startswith(prefix)}
    assert not bad, f"{layer}/{path.name} importa {bad}"


def test_tensorflow_is_imported_lazily():
    """TensorFlow solo se importa dentro de funciones (arranque rápido de la API y las pruebas)."""
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = [n for n in tree.body if isinstance(n, ast.Import | ast.ImportFrom)]
        for node in top_level:
            module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
            assert not (module or "").startswith("tensorflow"), f"{path.name} importa TF al cargar"


@pytest.mark.parametrize(
    "package", ["model", "controller", "view", "api", "grpc_api", "data", "tracking"]
)
def test_every_package_has_docstring(package):
    init = SRC / package / "__init__.py"
    assert ast.get_docstring(ast.parse(init.read_text(encoding="utf-8")))
