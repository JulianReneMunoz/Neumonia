"""Errores que la vista puede mostrar.

Se re-exportan aquí para que la vista no importe la capa Modelo.
"""

from neumonia.controller.gateways import GatewayError
from neumonia.model.classifier import ModelNotFoundError
from neumonia.model.readers import InvalidImageError

__all__ = ["GatewayError", "InvalidImageError", "ModelNotFoundError"]
