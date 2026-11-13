"""Prototipo de tomografía (spec 008, ADR-0010). Patrón AAA con volúmenes sintéticos.

Se escriben NIfTI con la misma convención de nombres que MEDPSeg; MEDPSeg real no se ejecuta aquí
(tarda minutos y vive en otro entorno): se simula su proceso con `monkeypatch`.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import numpy as np
import pytest

from neumonia.config import Settings
from neumonia.controller import ct_service
from neumonia.controller.ct_analysis import (
    CtReport,
    analyze,
    describe,
    lobe_severity,
)
from neumonia.model import ct_segmentation
from neumonia.model.ct_cache import load_case, save_case
from neumonia.model.ct_mesh import (
    LABEL_CONSOLIDATION,
    LABEL_GGO,
    Mesh,
    build_meshes,
    downsample_mask,
    mask_to_mesh,
    reduction_factor,
    slice_volumes,
    window_ct,
)
from neumonia.model.ct_segmentation import (
    STRUCTURES,
    CtSegmentation,
    MedpsegSegmenter,
    load_medpseg_output,
    python_in_env,
)
from neumonia.view.ct_views import (
    figure_3d,
    lobe_rows,
    most_affected_index,
    slice_image,
)

# El extra `ct` (nibabel + scikit-image) se instala con `make install` y en CI; sin él solo se
# omiten las pruebas que escriben NIfTI o calculan mallas.
needs_nibabel = pytest.mark.skipif(
    importlib.util.find_spec("nibabel") is None, reason="requiere el extra `ct`"
)
needs_skimage = pytest.mark.skipif(
    importlib.util.find_spec("skimage") is None, reason="requiere el extra `ct`"
)

SHAPE = (40, 30, 36)  # (x, y, z) en RAS+
SPACING = (2.0, 2.0, 2.5)


def synthetic_segmentation(lesion: bool = True) -> CtSegmentation:
    """Pulmón derecho del paciente a x alto (RAS+), lesión en su base, 5 lóbulos."""
    right = np.zeros(SHAPE, bool)
    left = np.zeros(SHAPE, bool)
    right[22:36, 6:24, 4:32] = True
    left[4:18, 6:24, 4:32] = True
    ggo = np.zeros(SHAPE, bool)
    cons = np.zeros(SHAPE, bool)
    if lesion:
        ggo[24:34, 8:22, 4:12] = True
        cons[26:30, 10:14, 4:8] = True
    lobes = np.zeros(SHAPE, np.uint8)
    lobes[4:18, :, 18:32][left[4:18, :, 18:32]] = 1  # superior izquierdo
    lobes[4:18, :, 4:18][left[4:18, :, 4:18]] = 2  # inferior izquierdo
    lobes[22:36, :, 22:32][right[22:36, :, 22:32]] = 3  # superior derecho
    lobes[22:36, :, 13:22][right[22:36, :, 13:22]] = 4  # medio derecho
    lobes[22:36, :, 4:13][right[22:36, :, 4:13]] = 5  # inferior derecho
    airway = np.zeros(SHAPE, bool)
    airway[19:21, 12:15, 20:36] = True
    vessels = np.zeros(SHAPE, bool)
    vessels[17:23, 14:18, 14:22] = True
    masks = {
        "pulmon_derecho": right,
        "pulmon_izquierdo": left,
        "vidrio_esmerilado": ggo,
        "consolidacion": cons,
        "via_aerea": airway,
        "vasos": vessels,
    }
    ct = np.where(right | left, -850, 40).astype(np.int16)
    return CtSegmentation("caso", SPACING, masks, lobes, ct)


def write_medpseg_like(out: Path, seg: CtSegmentation, case_id: str = "caso") -> None:
    """Guarda en LPS (como DICOM/ITK) para comprobar la reorientación a RAS+."""
    import nibabel as nib

    affine = np.diag([-SPACING[0], -SPACING[1], SPACING[2], 1.0])

    def save(array: np.ndarray, suffix: str, image_affine: np.ndarray = affine) -> None:
        lps = array[::-1, ::-1, :]  # RAS → LPS en los índices
        nib.save(
            nib.Nifti1Image(lps.astype(np.int16), image_affine), out / f"{case_id}{suffix}.nii.gz"
        )

    lr = np.zeros(SHAPE, np.int16)
    lr[seg.masks["pulmon_izquierdo"]] = 1
    lr[seg.masks["pulmon_derecho"]] = 2
    out.mkdir(parents=True, exist_ok=True)
    save(lr, "_lr_lung")
    save(seg.masks["vidrio_esmerilado"], "_ggo")
    save(seg.masks["consolidacion"], "_consolidation")
    save(seg.masks["via_aerea"], "_airway")
    save(seg.masks["vasos"], "_vessel")
    # Como MONAI en MEDPSeg: misma rejilla de vóxeles pero metadatos de orientación incorrectos
    broken = np.array([[0, -1, 0, 0], [-1, 0, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], float)
    save(seg.lobes, "_lobes", broken)
    save(seg.ct, "")


# --- Lectura de MEDPSeg ---------------------------------------------------------------------


@needs_nibabel
def test_load_medpseg_output_reorients_to_ras(tmp_path):
    # Arrange
    original = synthetic_segmentation()
    write_medpseg_like(tmp_path, original)
    # Act
    seg = load_medpseg_output(tmp_path, "caso", tmp_path / "caso.nii.gz")
    # Assert: en RAS+ el pulmón derecho del paciente tiene x mayor que el izquierdo
    right_x = np.nonzero(seg.masks["pulmon_derecho"])[0].mean()
    left_x = np.nonzero(seg.masks["pulmon_izquierdo"])[0].mean()
    assert right_x > left_x
    assert seg.spacing == pytest.approx(SPACING)
    assert np.array_equal(seg.masks["vidrio_esmerilado"], original.masks["vidrio_esmerilado"])
    assert np.array_equal(seg.lobes, original.lobes)
    assert seg.ct is not None


@needs_nibabel
def test_load_medpseg_output_tolerates_missing_optional_files(tmp_path):
    write_medpseg_like(tmp_path, synthetic_segmentation())
    for name in ("caso_ggo.nii.gz", "caso_lobes.nii.gz"):
        (tmp_path / name).unlink()
    seg = load_medpseg_output(tmp_path, "caso")
    assert not seg.masks["vidrio_esmerilado"].any()
    assert seg.lobes is None
    assert seg.ct is None


def test_load_medpseg_output_requires_lungs(tmp_path):
    with pytest.raises(FileNotFoundError, match="MEDPSeg"):
        load_medpseg_output(tmp_path, "nada")


def test_segmentation_validates_masks():
    with pytest.raises(ValueError, match="Faltan"):
        CtSegmentation("x", SPACING, {"pulmon_derecho": np.zeros(SHAPE, bool)})
    masks = {name: np.zeros(SHAPE, bool) for name in STRUCTURES}
    masks["vasos"] = np.zeros((2, 2, 2), bool)
    with pytest.raises(ValueError, match="misma forma"):
        CtSegmentation("x", SPACING, masks)


# --- Proceso externo MEDPSeg ----------------------------------------------------------------


@needs_nibabel
def test_medpseg_segmenter_runs_runner_and_reads_output(tmp_path, monkeypatch):
    # Arrange: el "proceso" de MEDPSeg escribe sus NIfTI y avisa con MEDPSEG_OK
    python = tmp_path / "python"
    python.write_text("")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        write_medpseg_like(Path(cmd[3]), synthetic_segmentation(), "estudio")
        return subprocess.CompletedProcess(cmd, 0, stdout="...\nMEDPSEG_OK 12 s\n", stderr="")

    monkeypatch.setattr(ct_segmentation.subprocess, "run", fake_run)
    # Act
    seg = MedpsegSegmenter(python, spacing=1.5).segment(tmp_path / "estudio.nii.gz", tmp_path / "o")
    # Assert
    assert calls[0][1].endswith("medpseg_runner.py")
    assert calls[0][-2:] == ["--spacing", "1.5"]
    assert seg.case_id == "estudio"
    assert seg.lesion.any()


def test_medpseg_segmenter_reports_failures(tmp_path, monkeypatch):
    python = tmp_path / "python"
    python.write_text("")
    monkeypatch.setattr(
        ct_segmentation.subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="sin memoria"),
    )
    with pytest.raises(RuntimeError, match="sin memoria"):
        MedpsegSegmenter(python).segment(tmp_path / "a.nii.gz", tmp_path / "o")
    with pytest.raises(FileNotFoundError, match="ct-setup"):
        MedpsegSegmenter(tmp_path / "no-existe").segment(tmp_path / "a.nii.gz", tmp_path / "o")


def test_python_in_env_points_inside_the_environment(tmp_path):
    path = python_in_env(tmp_path / "env")
    assert path.parent.parent == tmp_path / "env"
    assert path.name.startswith("python")


# --- Informe --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("percent", "score"),
    [(0, 0), (0.5, 0), (1, 1), (4.99, 1), (5, 2), (25, 2), (25.1, 3), (50, 3), (75, 4), (80, 5)],
)
def test_lobe_severity_bands(percent, score):
    assert lobe_severity(percent) == score


def test_analyze_quantifies_lesion_by_lung_and_lobe():
    # Act
    report = analyze(synthetic_segmentation())
    # Assert
    assert report.lesion_ml > 0
    assert report.percent_by_lung["pulmon_derecho"] > 0
    assert report.percent_by_lung["pulmon_izquierdo"] == 0
    worst = max(report.lobes, key=lambda lobe: lobe.percent)
    assert worst.name == "lobulo_inferior_derecho"
    assert report.severity_score == sum(lobe.score for lobe in report.lobes)
    assert report.consolidation_ml < report.ggo_ml
    text = " ".join(report.summary)
    assert "predominio derecho" in text
    assert "lóbulo inferior derecho" in text
    assert report.summary[-1].startswith("Prototipo de investigación")


def test_analyze_without_lesion_or_lobes():
    seg = synthetic_segmentation(lesion=False)
    seg = CtSegmentation(seg.case_id, seg.spacing, seg.masks, None, None)
    report = analyze(seg)
    assert report.lesion_ml == 0
    assert report.severity_score is None
    assert report.summary[0].startswith("No se segmentaron lesiones")


def test_report_roundtrip():
    report = analyze(synthetic_segmentation())
    restored = CtReport.from_dict(report.to_dict())
    assert restored == report


def test_minimal_findings_are_reported_as_noise():
    # Arrange: una mancha mínima en un pulmón grande (como en la tomografía sana de prueba)
    seg = synthetic_segmentation(lesion=False)
    seg.masks["vidrio_esmerilado"][29:31, 14:16, 19:21] = True
    # Act
    report = analyze(seg)
    # Assert
    assert 0 < report.percent_total < 1
    assert report.severity_score == 0
    assert "umbral de ruido" in report.summary[0]


def test_describe_bilateral():
    report = analyze(synthetic_segmentation())
    bilateral = CtReport(
        **{
            **report.to_dict(),
            "lobes": report.lobes,
            "percent_by_lung": {"pulmon_derecho": 10.0, "pulmon_izquierdo": 4.0},
        }
    )
    assert "bilateral" in describe(bilateral)[0]


# --- Mallas, cortes y caché -----------------------------------------------------------------


@needs_skimage
def test_downsample_and_mesh_are_in_millimetres():
    # Arrange
    mask = np.zeros((20, 20, 20), bool)
    mask[5:15, 5:15, 5:15] = True
    # Act
    small = downsample_mask(mask, 2)
    mesh = mask_to_mesh(mask, (1.0, 1.0, 2.0))
    # Assert
    assert small.shape == (10, 10, 10)
    assert small[5, 5, 5]
    assert not mesh.empty
    assert mesh.vertices[:, 2].max() == pytest.approx(29.0, abs=1.0)  # 14.5 vóxeles × 2 mm
    assert mask_to_mesh(np.zeros((5, 5, 5), bool), (1, 1, 1)).empty
    assert reduction_factor((300, 512, 512), 128) == 4


@needs_skimage
def test_build_meshes_and_slice_volumes():
    seg = synthetic_segmentation()
    meshes = build_meshes(seg, max_dim=20)
    ct, labels, spacing = slice_volumes(seg, max_dim=20)
    assert set(meshes) == set(STRUCTURES)
    assert not meshes["pulmon_derecho"].empty
    assert labels.max() == LABEL_CONSOLIDATION
    assert (labels == LABEL_GGO).any()
    assert spacing == (4.0, 4.0, 5.0)
    assert ct.dtype == np.uint8
    assert window_ct(np.array([-2000, -600, 500])).tolist() == [0, 127, 255]


def test_cache_roundtrip_and_version(tmp_path):
    # Arrange
    meshes = {"vasos": Mesh(np.ones((3, 3), np.float32), np.array([[0, 1, 2]], np.int32))}
    labels = np.zeros((4, 4, 4), np.uint8)
    # Act
    path = save_case(tmp_path / "c.npz", "c", meshes, {"a": 1}, labels, (1.0, 1.0, 1.0))
    case = load_case(path)
    # Assert
    assert case.case_id == "c"
    assert case.report == {"a": 1}
    assert case.ct is None
    assert case.meshes["vasos"].faces.tolist() == [[0, 1, 2]]
    data = dict(np.load(path))
    data["meta"] = np.frombuffer(b'{"version": 99}', dtype=np.uint8)
    np.savez_compressed(tmp_path / "viejo.npz", **data)
    with pytest.raises(ValueError, match="Versión"):
        load_case(tmp_path / "viejo.npz")


@needs_skimage
def test_service_caches_and_loads_cases(tmp_path):
    # Arrange
    class FakeSegmenter:
        def segment(self, ct_path, out_dir):
            return synthetic_segmentation()

    # Act
    path = ct_service.process(tmp_path / "caso.nii.gz", FakeSegmenter(), tmp_path / "w", tmp_path)
    case, report = ct_service.load(path)
    # Assert
    assert ct_service.available_cases(tmp_path) == {"caso": path}
    assert report.lesion_ml > 0
    assert case.ct is not None
    assert path.stat().st_size < 2_000_000


def test_build_ct_segmenter_from_settings(tmp_path, monkeypatch):
    assert ct_service.build_ct_segmenter(Settings()) is None
    monkeypatch.setenv("NEUMONIA_MEDPSEG_PYTHON", str(tmp_path / "py"))
    settings = Settings.from_env()
    assert settings.medpseg_python == tmp_path / "py"
    assert isinstance(ct_service.build_ct_segmenter(settings), MedpsegSegmenter)


# --- Vista ----------------------------------------------------------------------------------


@needs_skimage
def test_figure_3d_respects_visible_structures_and_labels_sides():
    meshes = build_meshes(synthetic_segmentation(), max_dim=20)
    full = figure_3d(meshes)
    lungs_only = figure_3d(meshes, ("pulmon_derecho", "pulmon_izquierdo"))
    assert len(full.data) == 6
    assert len(lungs_only.data) == 2
    texts = {a.text: a.x for a in full.layout.scene.annotations}
    assert texts["DERECHO"] > texts["IZQUIERDO"]  # x alto = derecho en RAS+
    assert full.layout.scene.camera.eye.y > 0  # vista anterior


@pytest.mark.parametrize("plane", ["axial", "coronal"])
def test_slice_image_shows_right_lung_on_screen_left(plane):
    # Arrange
    ct, labels, spacing = slice_volumes(synthetic_segmentation(), max_dim=64)
    index = most_affected_index(labels, plane)
    # Act
    image = slice_image(ct, labels, spacing, plane, index)
    # Assert: la lesión (derecho del paciente) cae en la mitad izquierda de la imagen
    yellowish = (image[..., 0] > 150) & (image[..., 2] < 140)
    cols = np.nonzero(yellowish)[1]
    assert image.dtype == np.uint8
    assert cols.size
    assert cols.mean() < image.shape[1] / 2


def test_slice_image_without_ct_and_invalid_plane():
    _, labels, spacing = slice_volumes(synthetic_segmentation(), max_dim=64)
    assert slice_image(None, labels, spacing, "axial", 5).ndim == 3
    with pytest.raises(ValueError, match="plane"):
        slice_image(None, labels, spacing, "sagital", 0)


def test_lobe_rows_table():
    rows = lobe_rows(analyze(synthetic_segmentation()))
    assert rows["Lóbulo"][0] == "Lóbulo superior derecho"
    assert len(rows["Puntaje (0–5)"]) == 5
