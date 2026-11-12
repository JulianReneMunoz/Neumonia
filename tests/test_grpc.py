"""Servidor gRPC en proceso con el servicio falso."""

from __future__ import annotations

import grpc
import pytest

from neumonia.controller.service import PneumoniaService
from neumonia.grpc_api import neumonia_pb2, neumonia_pb2_grpc
from neumonia.grpc_api.server import create_server
from tests.conftest import FakeClassifier, FakeExplainer


@pytest.fixture
def stub(settings):
    service = PneumoniaService(FakeClassifier(), FakeExplainer())
    server, port = create_server(lambda: service, settings, address="127.0.0.1:0")
    server.start()
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    yield neumonia_pb2_grpc.PneumoniaDetectorStub(channel)
    channel.close()
    server.stop(None)


def test_grpc_health(stub):
    reply = stub.Health(neumonia_pb2.HealthRequest())
    assert reply.status == "ok"


def test_grpc_predict(stub, png_bytes_sample):
    reply = stub.Predict(neumonia_pb2.PredictRequest(image=png_bytes_sample, filename="rx.png"))
    assert reply.label == "PNEUMONIA"
    assert reply.gradcam_png.startswith(b"\x89PNG")
    assert set(reply.class_probabilities) == {"bacteriana", "normal", "viral"}


@pytest.mark.parametrize("image", [b"", b"no-imagen"])
def test_grpc_invalid_argument(stub, image):
    with pytest.raises(grpc.RpcError) as info:
        stub.Predict(neumonia_pb2.PredictRequest(image=image, filename="x.txt"))
    assert info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
