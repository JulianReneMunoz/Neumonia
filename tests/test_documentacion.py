"""Integridad de la arquitectura documentada, el grafo (graphify) y la memoria (Engram)."""

from __future__ import annotations

import importlib.util
import json
import re

import pytest

from tests.conftest import ROOT

ARQ = ROOT / "docs" / "arquitectura"
DIAGRAMAS = sorted((ARQ / "diagramas").glob("*.mmd"))
ENGRAM_TYPES = {"decision", "architecture", "bugfix", "pattern", "config", "discovery", "learning"}


def _memorias():
    spec = importlib.util.spec_from_file_location(
        "engram_memoria", ROOT / "scripts" / "engram_memoria.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MEMORIAS


def test_there_are_twelve_diagrams():
    assert len(DIAGRAMAS) == 12


@pytest.mark.parametrize("mmd", DIAGRAMAS, ids=lambda p: p.stem)
def test_each_diagram_has_svg_export(mmd):
    svg = mmd.with_suffix(".svg")
    assert svg.is_file()
    assert svg.read_text(encoding="utf-8")[:200].lstrip().startswith("<svg")


@pytest.mark.parametrize("mmd", DIAGRAMAS, ids=lambda p: p.stem)
def test_each_diagram_is_referenced_in_design_index(mmd):
    index = (ARQ / "README.md").read_text(encoding="utf-8")
    assert f"diagramas/{mmd.stem}.svg" in index


def test_traceability_covers_23_methodologies():
    text = (ARQ / "METODOLOGIAS_ARQUITECTURA.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \|", text, flags=re.M)
    assert [int(r) for r in rows] == list(range(1, 24))


@pytest.mark.parametrize(
    "path",
    [
        "DESIGN.md",
        "METODOLOGIAS_ARQUITECTURA.md",
        "GRAFO_GRAPHIFY.md",
        "MEMORIA_ENGRAM.md",
        "README.md",
    ],
)
def test_architecture_documents_exist(path):
    assert (ARQ / path).stat().st_size > 1000


def test_engram_memories_are_valid_and_unique():
    memorias = _memorias()
    topics = [m[1] for m in memorias]
    assert len(memorias) == 19
    assert len(set(topics)) == len(topics)
    assert {m[0] for m in memorias} <= ENGRAM_TYPES
    assert all(m[2].strip() and m[3].strip() for m in memorias)


def test_engram_memories_contain_no_patient_data():
    text = json.dumps(_memorias(), ensure_ascii=False)
    assert "PatientName" not in text.replace("PatientID/PatientName nunca", "")


def test_engram_export_is_versioned():
    config = json.loads((ROOT / ".engram" / "config.json").read_text(encoding="utf-8"))
    assert config["project_name"] == "neumonia"
    assert list((ROOT / ".engram" / "chunks").glob("*.jsonl.gz"))


@pytest.mark.parametrize("name", ["graph.json", "GRAPH_REPORT.md", "graph.html", "graph.svg"])
def test_graphify_outputs_exist(name):
    assert (ROOT / "graphify-out" / name).is_file()


def test_graphify_reports_no_import_cycles():
    report = (ROOT / "graphify-out" / "GRAPH_REPORT.md").read_text(encoding="utf-8")
    cycles = report.split("## Import Cycles", 1)[1].split("##", 1)[0]
    assert "None detected" in cycles


def test_graphify_hooks_use_uv_for_windows():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for groups in settings["hooks"].values()
        for group in groups
        for hook in group["hooks"]
        if "graphify" in hook["command"]
    ]
    assert len(commands) == 3
    assert all(cmd.startswith("uv run graphify hook-guard") for cmd in commands)
