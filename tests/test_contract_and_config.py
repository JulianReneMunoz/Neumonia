"""Contrato documentado (openapi.yaml + ejemplo) y configuración por entorno."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neumonia.config import Settings
from tests.conftest import EXPECTED, ROOT

OPENAPI = ROOT / "api" / "openapi.yaml"


def test_expected_example_has_contract_keys():
    example = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert {"label", "probability", "gradcam_url"} <= set(example)
    assert example["label"] in {"NORMAL", "PNEUMONIA"}


@pytest.mark.parametrize(
    "fragment", ["/predict:", "/health:", "multipart/form-data", "'422'", "'500'", "gradcam_url"]
)
def test_openapi_yaml_documents_contract(fragment):
    assert fragment in OPENAPI.read_text(encoding="utf-8")


def test_settings_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("NEUMONIA_MODEL_PATH", str(tmp_path / "m.h5"))
    monkeypatch.setenv("NEUMONIA_THRESHOLD", "0.35")
    monkeypatch.setenv("NEUMONIA_API_URL", "http://api:8000")
    settings = Settings.from_env()
    assert settings.model_path == Path(tmp_path / "m.h5")
    assert settings.threshold == 0.35
    assert settings.api_url == "http://api:8000"


@pytest.mark.parametrize(
    ("kwargs", "message"), [({"threshold": 1.0}, "umbral"), ({"max_upload_mb": 0}, "positivo")]
)
def test_settings_validation(kwargs, message):
    with pytest.raises(ValueError, match=message):
        Settings(**kwargs)


@pytest.mark.parametrize(
    "pattern", ["*.h5", "*.pt", "*.onnx", "*.pkl", ".env", "mlruns/", "data/raw/", "runtime/"]
)
def test_gitignore_protects_weights_and_secrets(pattern):
    assert pattern in (ROOT / ".gitignore").read_text(encoding="utf-8")
