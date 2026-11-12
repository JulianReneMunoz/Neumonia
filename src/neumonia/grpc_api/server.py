"""Servidor gRPC sobre el mismo controlador que usa la API REST.

Los stubs `neumonia_pb2*.py` se generan con `make proto` desde `neumonia.proto`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent import futures

import grpc

from neumonia.config import Settings, get_settings
from neumonia.controller.report import png_bytes
from neumonia.controller.service import PneumoniaService
from neumonia.grpc_api import neumonia_pb2, neumonia_pb2_grpc
from neumonia.model.readers import InvalidImageError

logger = logging.getLogger("neumonia.grpc")


class PneumoniaDetectorServicer(neumonia_pb2_grpc.PneumoniaDetectorServicer):
    def __init__(self, service_factory: Callable[[], PneumoniaService], settings: Settings) -> None:
        self._factory = service_factory
        self._service: PneumoniaService | None = None
        self.settings = settings

    @property
    def service(self) -> PneumoniaService:
        if self._service is None:
            self._service = self._factory()
        return self._service

    def Predict(self, request, context):  # noqa: N802 - nombre impuesto por gRPC
        if not request.image:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Imagen vacía.")
        try:
            prediction = self.service.predict_bytes(request.image, request.filename or None)
        except InvalidImageError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return neumonia_pb2.PredictReply(
            label=prediction.label.value,
            probability=prediction.probability,
            subtype=prediction.subtype,
            class_probabilities=prediction.class_probabilities,
            gradcam_png=png_bytes(prediction.heatmap) if prediction.heatmap is not None else b"",
            model_version=self.settings.model_version,
        )

    def Health(self, request, context):  # noqa: N802
        return neumonia_pb2.HealthReply(status="ok", model_version=self.settings.model_version)


def create_server(
    service_factory: Callable[[], PneumoniaService] | None = None,
    settings: Settings | None = None,
    address: str = "[::]:50051",
    max_workers: int = 4,
) -> tuple[grpc.Server, int]:
    settings = settings or get_settings()
    if service_factory is None:
        from neumonia.controller.factory import get_service

        service_factory = get_service
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[("grpc.max_receive_message_length", int(settings.max_upload_mb * 1024 * 1024))],
    )
    neumonia_pb2_grpc.add_PneumoniaDetectorServicer_to_server(
        PneumoniaDetectorServicer(service_factory, settings), server
    )
    port = server.add_insecure_port(address)
    return server, port


def serve() -> None:  # pragma: no cover - punto de entrada de consola
    logging.basicConfig(level=logging.INFO)
    server, port = create_server()
    server.start()
    logger.info("gRPC escuchando en el puerto %s", port)
    server.wait_for_termination()
