"""Métricas, catálogo del dataset (RSNA / aula), evaluación con tracker y descarga del modelo."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile

import numpy as np
import pytest

from neumonia.controller.service import PneumoniaService
from neumonia.data.dataset import (
    Sample,
    extract_course_zips,
    load_rsna,
    read_metadata_csv,
    scan_folder,
    stratified_subset,
    subtype_from_name,
    summarize,
    write_metadata_csv,
)
from neumonia.evaluation import binary_metrics, evaluate, roc_auc, subgroup_metrics
from neumonia.model.download import ChecksumError, download_model, sha256_of
from neumonia.tracking.tracker import NullTracker, build_tracker
from tests.conftest import ROOT, FakeClassifier, FakeExplainer, make_dicom_bytes


# ---------- métricas ----------
def test_binary_metrics_perfect():
    m = binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert m["accuracy"] == 1.0
    assert m["recall"] == 1.0
    assert m["specificity"] == 1.0
    assert m["roc_auc"] == 1.0


def test_binary_metrics_confusion_counts():
    m = binary_metrics([1, 1, 0, 0], [0.9, 0.2, 0.7, 0.1])
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (1, 1, 1, 1)
    assert m["precision"] == 0.5
    assert m["f1"] == 0.5


@pytest.mark.parametrize(
    ("y", "s", "auc"),
    [
        ([0, 1], [0.2, 0.8], 1.0),
        ([0, 1], [0.8, 0.2], 0.0),
        ([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5], 0.5),
        ([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], 0.75),
    ],
)
def test_roc_auc_known_values(y, s, auc):
    assert roc_auc(np.array(y), np.array(s)) == pytest.approx(auc)


def test_roc_auc_single_class_is_none():
    assert roc_auc(np.array([1, 1]), np.array([0.2, 0.3])) is None


def test_binary_metrics_length_mismatch():
    with pytest.raises(ValueError, match="longitud"):
        binary_metrics([0, 1], [0.5])


def test_metrics_handle_no_positive_predictions():
    m = binary_metrics([1, 0], [0.1, 0.1])
    assert m["precision"] is None
    assert m["f1"] is None


def test_subgroup_metrics_by_sex():
    rows = [
        {"sex": "F", "target": 1, "p_pneumonia": 0.9},
        {"sex": "M", "target": 1, "p_pneumonia": 0.1},
        {"sex": "", "target": 0, "p_pneumonia": 0.2},
    ]
    groups = subgroup_metrics(rows, "sex")
    assert groups["F"]["recall"] == 1.0
    assert groups["M"]["recall"] == 0.0
    assert "desconocido" in groups


# ---------- dataset ----------
@pytest.mark.parametrize(
    ("name", "subtype"),
    [
        ("person1711_bacteria_4527.jpeg", "bacteriana"),
        ("person1500_virus_2610.jpeg", "viral"),
        ("viral (3).dcm", "viral"),
        ("NORMAL2-IM-1147-0001.jpeg", "normal"),
        ("otra.png", None),
    ],
)
def test_subtype_from_name(name, subtype):
    assert subtype_from_name(name) == subtype


@pytest.fixture(scope="module")
def course_dir(tmp_path_factory):
    return extract_course_zips(ROOT / "data", tmp_path_factory.mktemp("course"))


def test_course_zips_are_cataloged(course_dir):
    samples = scan_folder(course_dir)
    assert len(samples) == 16
    assert sum(s.target for s in samples) == 10


def test_course_dicoms_have_metadata(course_dir):
    dicoms = [s for s in scan_folder(course_dir) if s.image_path.endswith(".dcm")]
    assert len(dicoms) == 4
    assert all({"age", "sex", "view_position"} <= set(s.metadata) for s in dicoms)


def test_extract_rejects_zip_slip(tmp_path):
    archive = tmp_path / "JPG.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "x")
    with pytest.raises(ValueError, match="insegura"):
        extract_course_zips(tmp_path, tmp_path / "out")


@pytest.fixture
def rsna_dir(tmp_path, gradient_image):
    """Réplica mínima de la estructura del RSNA (stage 2) con 3 pacientes."""
    images = tmp_path / "stage_2_train_images"
    images.mkdir()
    with (tmp_path / "stage_2_train_labels.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(["patientId", "x", "y", "width", "height", "Target"])
        w.writerows(
            [
                ["p1", "", "", "", "", 0],
                ["p2", 10, 10, 50, 50, 1],
                ["p2", 100, 10, 50, 50, 1],
                ["p3", "", "", "", "", 0],
            ]
        )
    with (tmp_path / "stage_2_detailed_class_info.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(["patientId", "class"])
        w.writerows(
            [["p1", "Normal"], ["p2", "Lung Opacity"], ["p3", "No Lung Opacity / Not Normal"]]
        )
    for pid, sex, view in (("p1", "F", "PA"), ("p2", "M", "AP"), ("p3", "F", "AP")):
        (images / f"{pid}.dcm").write_bytes(make_dicom_bytes(gradient_image, sex=sex, view=view))
    return tmp_path


def test_load_rsna_merges_labels_classes_and_headers(rsna_dir):
    samples = {s.image_path.split("/")[-1].split("\\")[-1]: s for s in load_rsna(rsna_dir)}
    assert samples["p2.dcm"].target == 1
    assert samples["p2.dcm"].n_boxes == 2
    assert samples["p3.dcm"].rsna_class.startswith("No Lung Opacity")
    assert samples["p1.dcm"].metadata["sex"] == "F"


def test_load_rsna_limit_and_missing(rsna_dir, tmp_path_factory):
    assert len(load_rsna(rsna_dir, limit=1)) == 1
    with pytest.raises(FileNotFoundError, match="dataset-rsna"):
        load_rsna(tmp_path_factory.mktemp("vacio"))


def _samples(n_pos: int, n_neg: int) -> list[Sample]:
    return [Sample(f"p{i}", "t", 1) for i in range(n_pos)] + [
        Sample(f"n{i}", "t", 0) for i in range(n_neg)
    ]


def test_stratified_subset_keeps_proportion():
    subset = stratified_subset(_samples(300, 700), 100)
    assert len(subset) == 100
    assert sum(s.target for s in subset) == 30


def test_stratified_subset_is_reproducible():
    data = _samples(50, 50)
    assert [s.image_path for s in stratified_subset(data, 10, seed=7)] == [
        s.image_path for s in stratified_subset(data, 10, seed=7)
    ]


def test_stratified_subset_larger_than_data():
    assert len(stratified_subset(_samples(2, 2), 10)) == 4


def test_metadata_csv_roundtrip(tmp_path):
    samples = [Sample("a.dcm", "rsna", 1, "neumonia", "Lung Opacity", 2, {"age": 70, "sex": "F"})]
    rows = read_metadata_csv(write_metadata_csv(samples, tmp_path / "m.csv"))
    assert rows[0]["age_group"] == "65+"
    assert rows[0]["n_boxes"] == "2"


def test_summarize():
    summary = summarize([Sample("a", "t", 1, metadata={"sex": "F"}), Sample("b", "t", 0)])
    assert summary["prevalencia"] == 0.5
    assert summary["por_sexo"] == {"F": 1, "desconocido": 1}


# ---------- evaluación + tracking ----------
class RecordingTracker(NullTracker):
    def __init__(self):
        self.params, self.metrics, self.artifacts = {}, {}, []

    def log_params(self, params):
        self.params.update(params)

    def log_metrics(self, metrics):
        self.metrics.update(metrics)

    def log_artifact(self, path):
        self.artifacts.append(path.name)


def test_evaluate_logs_metrics_and_artifacts(course_dir, tmp_path):
    # Arrange
    service = PneumoniaService(FakeClassifier((0.7, 0.2, 0.1)), FakeExplainer())
    tracker = RecordingTracker()
    samples = scan_folder(course_dir)
    # Act
    result = evaluate(service, samples, tracker, tmp_path / "out", gradcam_examples=2)
    # Assert
    assert result.metrics["n"] == 16
    assert result.metrics["recall"] == 1.0  # el doble siempre dice neumonía
    assert tracker.params["n_samples"] == 16
    assert {"predictions.csv", "metrics.json"} <= set(tracker.artifacts)
    assert sum(a.startswith("gradcam_") for a in tracker.artifacts) == 2
    assert "sex" in json.loads((tmp_path / "out" / "metrics.json").read_text())["subgroups"]


def test_evaluate_skips_missing_files(tmp_path):
    service = PneumoniaService(FakeClassifier())
    result = evaluate(service, [Sample(str(tmp_path / "no.png"), "t", 1)], NullTracker(), tmp_path)
    assert result.skipped == 1


def test_build_tracker_without_uri_is_null():
    assert isinstance(build_tracker(None), NullTracker)


def test_mlflow_tracker_writes_run(tmp_path):
    pytest.importorskip("mlflow")
    import mlflow

    db = tmp_path / "mlflow.db"
    tracker = build_tracker(f"sqlite:///{db.as_posix()}", experiment="prueba")
    with tracker.run("r1"):
        tracker.log_params({"a": 1})
        tracker.log_metrics({"recall__age_group__65+": 0.5})
    runs = mlflow.search_runs(experiment_names=["prueba"])
    assert db.is_file()
    assert runs.loc[0, "metrics.recall__age_group__65plus"] == 0.5


# ---------- descarga del modelo ----------
def test_download_model_from_file_url(tmp_path):
    src = tmp_path / "src.h5"
    src.write_bytes(b"pesos")
    dest = download_model(
        src.as_uri(), tmp_path / "m" / "model.h5", hashlib.sha256(b"pesos").hexdigest()
    )
    assert dest.read_bytes() == b"pesos"


def test_download_model_checksum_mismatch(tmp_path):
    src = tmp_path / "src.h5"
    src.write_bytes(b"alterado")
    with pytest.raises(ChecksumError):
        download_model(src.as_uri(), tmp_path / "model.h5", "0" * 64)
    assert not (tmp_path / "model.h5.part").exists()


def test_download_model_skips_valid_existing(tmp_path):
    dest = tmp_path / "model.h5"
    dest.write_bytes(b"ok")
    assert download_model("https://no.se.usa", dest, sha256_of(dest)) == dest


def test_download_model_rejects_http(tmp_path):
    with pytest.raises(ValueError, match="https"):
        download_model("http://inseguro/model.h5", tmp_path / "x.h5", None)
