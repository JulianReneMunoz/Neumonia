"""API REST con FastAPI — adaptador de entrega sobre el controlador.

Contrato (api/openapi.yaml):
    GET  /health   → 200 {status, model_loaded, model_version}
    POST /predict  → 200 {label, probability, gradcam_url, ...} | 422 entrada inválida | 500 {error}
    GET  /static/gradcam/{id}.png → imagen Grad-CAM

El frontend desacoplado (`frontend/`, spec 012) consume esta API desde otro origen: por eso hay
CORS para los orígenes de `NEUMONIA_CORS_ORIGINS`. El modelo se carga una sola vez al arrancar
(lifespan); si falta el archivo, la API arranca igual y `/health` responde `model_loaded: false`.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from neumonia import __version__
from neumonia.api.schemas import ErrorResponse, HealthResponse, PredictionResponse
from neumonia.config import Settings, get_settings
from neumonia.controller.report import png_bytes
from neumonia.controller.service import PneumoniaService
from neumonia.model.readers import InvalidImageError

logger = logging.getLogger("neumonia.api")


def _prune(directory: Path, keep: int) -> None:
    files = sorted(directory.glob("*.png"), key=lambda p: p.stat().st_mtime)
    for old in files[: max(0, len(files) - keep)]:
        old.unlink(missing_ok=True)


def warm_up(service: Callable[[], PneumoniaService]) -> bool:
    """Carga el modelo una vez al arrancar. Si falla, la API sigue viva y /health lo reporta."""
    try:
        classifier = service().classifier
        getattr(classifier, "model", None)  # KerasClassifier carga el .h5 al leer `model`
    except Exception as exc:  # arrancar sin modelo es mejor que no arrancar
        logger.warning("El modelo no se pudo cargar al arrancar: %s", exc)
        return False
    return True


def create_app(
    service_factory: Callable[[], PneumoniaService] | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    if service_factory is None:
        from neumonia.controller.factory import get_service

        service_factory = get_service

    gradcam_dir = settings.static_dir / "gradcam"
    gradcam_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, PneumoniaService] = {}

    def service() -> PneumoniaService:
        if "svc" not in state:
            state["svc"] = service_factory()
        return state["svc"]

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        warm_up(service)
        yield

    app = FastAPI(
        title="Neumonía — Inference API",
        version=__version__,
        description="Detección de neumonía en radiografías de tórax con Grad-CAM. Uso académico.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time-ms"],
    )
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    @app.middleware("http")
    async def timing(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-ms"] = f"{elapsed:.1f}"
        logger.info(
            "%s %s %s %.1fms", request.method, request.url.path, response.status_code, elapsed
        )
        return response

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado: %s", exc)
        return JSONResponse(status_code=500, content={"error": "Error interno del modelo."})

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        svc = state.get("svc")
        loaded = bool(svc and getattr(svc.classifier, "is_loaded", True))
        return HealthResponse(
            status="ok", model_loaded=loaded, model_version=settings.model_version
        )

    @app.post(
        "/predict",
        response_model=PredictionResponse,
        responses={422: {"description": "Entrada inválida"}, 500: {"model": ErrorResponse}},
    )
    async def predict(file: UploadFile = File(...)) -> PredictionResponse:  # noqa: B008
        data = await file.read()
        if not data:
            raise HTTPException(
                status_code=422, detail=[{"loc": ["body", "file"], "msg": "Archivo vacío."}]
            )
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(
                status_code=422,
                detail=[{"loc": ["body", "file"], "msg": f"Supera {settings.max_upload_mb} MB."}],
            )
        try:
            prediction = service().predict_bytes(data, file.filename)
        except InvalidImageError as exc:
            raise HTTPException(
                status_code=422, detail=[{"loc": ["body", "file"], "msg": str(exc)}]
            ) from exc

        request_id = uuid.uuid4().hex
        gradcam_url = None
        if prediction.heatmap is not None:
            (gradcam_dir / f"{request_id}.png").write_bytes(png_bytes(prediction.heatmap))
            _prune(gradcam_dir, settings.max_gradcam_files)
            gradcam_url = f"/static/gradcam/{request_id}.png"
        payload = prediction.to_contract(gradcam_url, settings.model_version)
        return PredictionResponse(**payload, request_id=request_id)

    return app


def run() -> None:  # pragma: no cover - punto de entrada de consola
    import os

    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "neumonia.api.app:create_app",
        factory=True,
        host=os.environ.get("HOST", "0.0.0.0"),  # noqa: S104 - el contenedor debe escuchar fuera
        port=int(os.environ.get("PORT", "8000")),
    )
