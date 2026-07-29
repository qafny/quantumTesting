import logging
from typing import Dict, List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from evaluators.base import BaseEvaluator
from evaluators.basis import QETGateSetBasis
from qetast.simulators import QETSimulator
from qucheck.coordinator import Coordinator
from qucheck.property import Property
from qucheck.test_runner import TestRunner
import evaluators.utils as eval_utils
import helpers.qubits as helper_qubits


class QuCheckEvaluator(BaseEvaluator):

    def __init__(self, qc: QuantumCircuit, optimization_level: int, **kwargs):
        logging.info("Initialising QuCheckEvaluator")
        super(QuCheckEvaluator, self).__init__(qc, QETGateSetBasis(), optimization_level)

        logging.info("Initialising QuCheck AerSimulator")
        self.backend = AerSimulator(method = "statevector")
        logging.info("Finished Initialising QuCheck AerSimulator")

        logging.info("Finished Initializing QuCheckEvaluator")

    @staticmethod
    def get_identifier():
        return "qchk"

    def evaluate(self, ins: Dict[str, bool]) -> List[Tuple[complex, Dict[str, bool]]]:
        logging.info("Evaluating using QuCheckEvaluator")

        '''
        Currently, we simply use the QETSimualator and return the results. But,
        TODO:
            1. Prapare the initial state using the ins dict.
            2. Run the AerSimulator on the prepared initial state
            3. Store the properties for the use in the comparator

            Docs:  https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html
        '''

        initial_state = helper_qubits.get_system_state_from_qubits(ins)

        simulator = QETSimulator(initial_state)
        simulator.visitRoot(self.get_circuit_ast())

        state = []
        for (amp, sd) in simulator.state:
            amp = eval_utils.zcomplex(amp)

            # We eliminate 0 amplitude basis-kets.
            if amp == 0:
                continue

            state.append((amp, sd))

        logging.info("Finished Evaluating using QuCheckEvaluator")

        return state
