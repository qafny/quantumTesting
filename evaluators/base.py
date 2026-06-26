import logging
from abc import ABC, abstractmethod
from typing import Dict, List
from qiskit import QuantumCircuit
from evaluators.basis import GateSetBasis
import helpers.qiskit as helpers_qiskit
import helpers.ast as helpers_ast
from globals import TagProcessor
from qetast.markers import PrefixedHadamardGatesMarker, SuffixedHadamardGatesMarker, MeasureGateMarker
from qetast.nodes import QXRoot
from qetast.processors import MarkedNodeEliminator


class BaseEvaluator(ABC):

    def __init__(self, qc: QuantumCircuit, gateset_basis: GateSetBasis, optimization_level: int):
        self._qc: QuantumCircuit = qc
        self._gateset_basis: GateSetBasis = gateset_basis
        self._optimization_level: int = optimization_level

        logging.info("Parsing Circuit")
        tqc, ast = helpers_qiskit.parse_qiskit_circuit(self._qc, self._gateset_basis, self._optimization_level)
        logging.info("Finished Parsing Circuit")

        logging.info("Applying Markers")
        ast = helpers_ast.get_applied_ast(ast, self._get_ast_markers())
        logging.info("Finished Applying Markers")

        logging.info("Applying Processors")
        ast = helpers_ast.get_applied_ast(ast, self._get_ast_processors())
        logging.info("Finished Applying Processors")

        self._tqc: QuantumCircuit = tqc
        self._ast: QXRoot = ast

    def _get_ast_markers(self):
        markers = []

        if TagProcessor().remove_prefixed_hadamards():
            markers.append(PrefixedHadamardGatesMarker())
        if TagProcessor().remove_suffixed_hadamards():
            markers.append(SuffixedHadamardGatesMarker())
        if TagProcessor().remove_measure():
            markers.append(MeasureGateMarker())

        return markers

    def _get_ast_processors(self):
        return [
            MarkedNodeEliminator()
        ]

    @staticmethod
    @abstractmethod
    def get_identifier() -> str:
        pass

    def get_circuit(self) -> QuantumCircuit:
        return self._qc

    def get_parsed_circuit(self) -> QuantumCircuit:
        return self._tqc

    def get_gateset_basis(self) -> GateSetBasis:
        return self._gateset_basis

    def get_circuit_ast(self) -> QXRoot:
        return self._ast

    def get_optimization_level(self) -> int:
        return self._optimization_level

    @abstractmethod
    def evaluate(self, ins: Dict[str, bool]):
        pass
