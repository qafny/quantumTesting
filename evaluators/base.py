import logging
from abc import ABC, abstractmethod
from typing import Dict
from qiskit import QuantumCircuit
from evaluators.basis import GateSetBasis
from parser.utils.qiskit_utils import parse_qiskit_circuit
from qetast.nodes import QXRoot


class BaseEvaluator(ABC):

    def __init__(self, qc: QuantumCircuit, gateset_basis: GateSetBasis):
        self._qc: QuantumCircuit = qc
        self._gateset_basis: GateSetBasis = gateset_basis

        logging.info("Parsing Circuit")
        tqc, ast = parse_qiskit_circuit(self._qc, self._gateset_basis)
        logging.info("Finished Parsing Circuit")

        self._tqc: QuantumCircuit = qc
        self._ast: QXRoot = ast

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

    @abstractmethod
    def evaluate(self, ins: Dict[str, bool]):
        pass
