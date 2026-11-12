"""Seguimiento de experimentos — DIP sobre MLflow.

`evaluate()` habla con el protocolo `Tracker`. En producción se inyecta `MlflowTracker`
(file store `./mlruns` o servidor `MLFLOW_TRACKING_URI`); en pruebas, `NullTracker` o un
doble que registra las llamadas.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol


class Tracker(Protocol):
    def run(self, run_name: str) -> Any: ...

    def log_params(self, params: dict[str, Any]) -> None: ...

    def log_metrics(self, metrics: dict[str, float]) -> None: ...

    def log_artifact(self, path: Path) -> None: ...


class NullTracker:
    """No registra nada. Útil cuando MLflow no está instalado."""

    @contextmanager
    def run(self, run_name: str) -> Iterator[None]:
        yield None

    def log_params(self, params: dict[str, Any]) -> None:
        return None

    def log_metrics(self, metrics: dict[str, float]) -> None:
        return None

    def log_artifact(self, path: Path) -> None:
        return None


class MlflowTracker:
    def __init__(
        self, tracking_uri: str, experiment: str = "neumonia-evaluacion", tags: dict | None = None
    ):
        import mlflow

        self._mlflow = mlflow
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment)
        self.tags = tags or {}

    @contextmanager
    def run(self, run_name: str) -> Iterator[Any]:
        with self._mlflow.start_run(run_name=run_name) as active:
            if self.tags:
                self._mlflow.set_tags(self.tags)
            yield active

    def log_params(self, params: dict[str, Any]) -> None:
        self._mlflow.log_params({k: str(v)[:500] for k, v in params.items()})

    def log_metrics(self, metrics: dict[str, float]) -> None:
        self._mlflow.log_metrics({k.replace("+", "plus"): float(v) for k, v in metrics.items()})

    def log_artifact(self, path: Path) -> None:
        self._mlflow.log_artifact(str(path))


def build_tracker(tracking_uri: str | None, **kwargs: Any) -> Tracker:
    if not tracking_uri:
        return NullTracker()
    try:
        return MlflowTracker(tracking_uri, **kwargs)
    except ImportError:
        return NullTracker()
