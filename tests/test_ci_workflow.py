"""SPEC-015: el job docker del CI libera disco antes de construir la imagen CPU."""

from __future__ import annotations

from tests.conftest import ROOT

CI = ROOT / ".github" / "workflows" / "ci.yml"


def _docker_job(text: str) -> str:
    return text.split("\n  docker:\n", 1)[1]


def test_docker_job_frees_disk_before_building_the_image():
    # Arrange
    job = _docker_job(CI.read_text(encoding="utf-8"))
    # Act
    free = job.find("name: Liberar espacio en disco")
    build = job.find("name: Build imagen CPU")
    step = job[free:build]
    # Assert
    assert 0 <= free < build
    for path in (
        "/usr/share/dotnet",
        "/usr/local/lib/android",
        "/opt/ghc",
        "/opt/hostedtoolcache/CodeQL",
    ):
        assert path in step
    assert "docker system prune -af" in step
    assert step.count("df -h /") == 2
