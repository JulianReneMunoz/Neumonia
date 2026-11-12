"""Política de decisión — patrón Estrategia sobre la regla de negocio.

El modelo entrega 3 clases (bacteriana, normal, viral) y el contrato del curso exige una
etiqueta binaria (NORMAL | PNEUMONIA). La política convierte una cosa en la otra:

    P(neumonía) = P(bacteriana) + P(viral)
    label = PNEUMONIA si P(neumonía) >= umbral, en otro caso NORMAL

Se suman las probabilidades en vez de tomar el argmax porque el argmax de 3 clases puede
decir "normal" con 0.40 mientras la neumonía acumula 0.60. El umbral es configurable para
priorizar sensibilidad (tamizaje) sobre especificidad, decisión que se documenta en la
Model Card.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from neumonia.config import CLASS_NAMES, NORMAL_INDEX
from neumonia.domain import Label


@dataclass(frozen=True)
class Decision:
    label: Label
    probability: float
    subtype: str
    target_index: int  # clase sobre la que se calcula Grad-CAM


class DecisionPolicy(Protocol):
    def decide(self, probs: np.ndarray) -> Decision: ...


class ThresholdPolicy:
    def __init__(
        self,
        threshold: float = 0.5,
        class_names: tuple[str, ...] = CLASS_NAMES,
        normal_index: int = NORMAL_INDEX,
    ) -> None:
        if not 0.0 < threshold < 1.0:
            raise ValueError("El umbral debe estar en (0, 1).")
        self.threshold = threshold
        self.class_names = class_names
        self.normal_index = normal_index

    def decide(self, probs: np.ndarray) -> Decision:
        probs = np.asarray(probs, dtype=np.float64)
        if probs.shape != (len(self.class_names),):
            raise ValueError(
                f"Se esperaban {len(self.class_names)} probabilidades, llegó {probs.shape}."
            )
        if np.any(probs < 0) or not np.isclose(probs.sum(), 1.0, atol=1e-3):
            raise ValueError("El vector de probabilidades no es una distribución válida.")
        p_normal = float(probs[self.normal_index])
        p_pneumonia = 1.0 - p_normal
        if p_pneumonia >= self.threshold:
            masked = probs.copy()
            masked[self.normal_index] = -1.0
            index = int(np.argmax(masked))
            return Decision(Label.PNEUMONIA, p_pneumonia, self.class_names[index], index)
        return Decision(
            Label.NORMAL, p_normal, self.class_names[self.normal_index], self.normal_index
        )
