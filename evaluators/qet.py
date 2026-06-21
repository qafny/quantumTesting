import logging
from typing import Dict
from qiskit import QuantumCircuit
from evaluators.base import BaseEvaluator
from evaluators.basis import QETGateSetBasis
from helpers.qubits import get_system_state_from_qubits
from qetast.simulators import QETSimulator
import evaluators.utils as eval_utils


class QETEvaluator(BaseEvaluator):

    def __init__(self, qc: QuantumCircuit):
        logging.info("Initializing QETEvaluator")
        super(QETEvaluator, self).__init__(qc, QETGateSetBasis())
        logging.info("Finished Initializing QETEvaluator")

    @staticmethod
    def get_identifier():
        return "qet"

    def evaluate(self, ins: Dict[str, bool]):
        logging.info("Evaluating using QETEvaluator")
        initial_state = get_system_state_from_qubits(ins)

        simulator = QETSimulator(initial_state)
        simulator.visitRoot(self.get_circuit_ast())

        state = []
        for (amp, sd) in simulator.state:
            amp = eval_utils.zcomplex(amp)
            state.append((amp, sd))

        logging.info("Finished Evaluating using QETEvaluator")

        return state
