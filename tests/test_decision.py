"""Política de decisión 3 clases → contrato binario NORMAL | PNEUMONIA."""

from __future__ import annotations

import numpy as np
import pytest

from neumonia.controller.decision import ThresholdPolicy
from neumonia.domain import Label


@pytest.mark.parametrize(
    ("probs", "label", "probability", "subtype", "target"),
    [
        ((0.7, 0.2, 0.1), Label.PNEUMONIA, 0.8, "bacteriana", 0),
        ((0.1, 0.2, 0.7), Label.PNEUMONIA, 0.8, "viral", 2),
        ((0.1, 0.8, 0.1), Label.NORMAL, 0.8, "normal", 1),
        ((0.3, 0.4, 0.3), Label.PNEUMONIA, 0.6, "bacteriana", 0),  # argmax diría "normal"
        ((0.25, 0.5, 0.25), Label.PNEUMONIA, 0.5, "bacteriana", 0),  # empate en el umbral
        ((0.0, 1.0, 0.0), Label.NORMAL, 1.0, "normal", 1),
        ((0.5, 0.0, 0.5), Label.PNEUMONIA, 1.0, "bacteriana", 0),
    ],
)
def test_threshold_policy_default(probs, label, probability, subtype, target):
    decision = ThresholdPolicy().decide(np.array(probs))
    assert decision.label is label
    assert decision.probability == pytest.approx(probability)
    assert decision.subtype == subtype
    assert decision.target_index == target


@pytest.mark.parametrize(
    ("threshold", "expected"), [(0.3, Label.PNEUMONIA), (0.5, Label.PNEUMONIA), (0.7, Label.NORMAL)]
)
def test_threshold_is_configurable(threshold, expected):
    # Arrange: P(neumonía) = 0.6
    probs = np.array([0.4, 0.4, 0.2])
    # Act / Assert
    assert ThresholdPolicy(threshold).decide(probs).label is expected


@pytest.mark.parametrize("threshold", [0.0, 1.0, -0.1, 1.5])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="umbral"):
        ThresholdPolicy(threshold)


@pytest.mark.parametrize(
    "probs", [(0.5, 0.5), (0.2, 0.2, 0.2), (-0.1, 0.6, 0.5), (0.5, 0.5, 0.5, 0.5)]
)
def test_rejects_invalid_distributions(probs):
    with pytest.raises(ValueError, match=r"probabilidades|distribución"):
        ThresholdPolicy().decide(np.array(probs))
