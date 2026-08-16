import logging
from typing import Dict, List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from evaluators.base import BaseEvaluator
from evaluators.basis import QETGateSetBasis
import evaluators.utils as eval_utils


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

        n_qubits = self.get_parsed_circuit().num_qubits

        qc = QuantumCircuit(n_qubits)
        for i, bit in ins.items():
            if bit:
                qc.x(int(i))
        qc.compose(self.get_parsed_circuit(), inplace=True)

        qc.save_statevector()
        job = self.backend.run(qc)
        result = job.result()
        sv = result.get_statevector(qc)

        state = []
        for i, amp in enumerate(sv):
            amp = eval_utils.zcomplex(amp)

            # We eliminate 0 amplitude basis-kets.
            if amp == 0:
                continue
            sd = {}
            for q in range(n_qubits):
                sd[str(q)] = bool((i >> q) & 1)
            state.append((amp, sd))

        logging.info("Finished Evaluating using QuCheckEvaluator")

        return state
