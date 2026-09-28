"""
Circuit-specific properties for qcp comparator.
"""

from typing import List

from .base import CircuitProperty, PropertyResult
from .properties import (
    AddersProperty,
    IntegerComparatorProperty,
    MultiplierProperty,
    WeightedAdderProperty,
    QuadraticFormProperty,
    PauliRotationProperty,
    ExactReciprocalProperty,
    InnerProductProperty,
    BitwiseProperty,
    ShiftProperty,
    RcAdderProperty,
    RcModularProperty,
    AdvancedMultiplyProperty,
    AdvancedSquareProperty,
    AdvancedDivideProperty,
    ControlledAdvancedMultiplyProperty,
)

_ALL_PROPERTIES: List[CircuitProperty] = [
    AddersProperty(),
    IntegerComparatorProperty(),
    MultiplierProperty(),
    WeightedAdderProperty(),
    QuadraticFormProperty(),
    PauliRotationProperty(),
    ExactReciprocalProperty(),
    InnerProductProperty(),
    BitwiseProperty(),
    ShiftProperty(),
    RcAdderProperty(),
    RcModularProperty(),
    AdvancedMultiplyProperty(),
    ControlledAdvancedMultiplyProperty(),
    AdvancedSquareProperty(),
    AdvancedDivideProperty(),
]


def get_properties_for_circuit(circuit, circuit_id: str) -> List[CircuitProperty]:
    applicable: List[CircuitProperty] = []
    for prop in _ALL_PROPERTIES:
        try:
            if prop.applies(circuit, circuit_id):
                applicable.append(prop)
        except Exception:
            continue
    return applicable


__all__ = ["CircuitProperty", "PropertyResult", "get_properties_for_circuit"]