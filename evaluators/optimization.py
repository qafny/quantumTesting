import logging

from typing import Dict
from qiskit import QuantumCircuit

from evaluators.base import BaseEvaluator
from evaluators.basis import QETGateSetBasis
from helpers.qubits import get_system_state_from_qubits
from qetast.simulators import QETSimulator

import evaluators.utils as eval_utils


class _QiskitCompilerOptimizationEvaluator(BaseEvaluator):

    def __init__(self, qc: QuantumCircuit, optimization_level: int):
        super(_QiskitCompilerOptimizationEvaluator, self).__init__(
            qc,
            QETGateSetBasis(),
            optimization_level
        )

    def evaluate(self, ins: Dict[str, bool]):
        initial_state = get_system_state_from_qubits(ins)

        simulator = QETSimulator(initial_state)
        simulator.visitRoot(self.get_circuit_ast())

        state = []

        for (amp, sd) in simulator.state:
            amp = eval_utils.zcomplex(amp)

            # Eliminate zero-amplitude basis kets.
            if amp == 0:
                continue

            state.append((amp, sd))

        return state


class QiskitCompilerOptimizationLevelZero(
        _QiskitCompilerOptimizationEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        logging.info(
            "Initializing QiskitCompilerOptimizationLevelZero"
        )
        super().__init__(qc, optimization_level=0)

    @staticmethod
    def get_identifier():
        return "qopt0"


class QiskitCompilerOptimizationLevelOne(
        _QiskitCompilerOptimizationEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        logging.info(
            "Initializing QiskitCompilerOptimizationLevelOne"
        )
        super().__init__(qc, optimization_level=1)

    @staticmethod
    def get_identifier():
        return "qopt1"


class QiskitCompilerOptimizationLevelTwo(
        _QiskitCompilerOptimizationEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        logging.info(
            "Initializing QiskitCompilerOptimizationLevelTwo"
        )
        super().__init__(qc, optimization_level=2)

    @staticmethod
    def get_identifier():
        return "qopt2"


class QiskitCompilerOptimizationLevelThree(
        _QiskitCompilerOptimizationEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        logging.info(
            "Initializing QiskitCompilerOptimizationLevelThree"
        )
        super().__init__(qc, optimization_level=3)

    @staticmethod
    def get_identifier():
        return "qopt3"