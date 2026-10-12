from typing import Any, Dict, List

from qiskit import QuantumCircuit

from comparators.base import BaseComparator
from evaluators.qet import QETEvaluator
import helpers.qubits as helper_qubits


class OptimizationPassComparator(BaseComparator):

    def __init__(
        self,
        circuit: QuantumCircuit,
        evaluator_classes: List[type[QETEvaluator]],
        inputs: List[Dict[str, bool]],
    ):
        # Construct each pass evaluator once.
        # Its constructor transforms the circuit and prepares it for QET.
        evaluators = [
            evaluator_class(qc=circuit.copy())
            for evaluator_class in evaluator_classes
        ]

        super().__init__(evaluators=evaluators, inputs=inputs)

        self._reference_evaluator = QETEvaluator(
            qc=circuit.copy(),
            optimization_level=0,
        )

    @staticmethod
    def get_identifier() -> str:
        return "optpass"

    def compare(self) -> List[Dict[str, Any]]:
        inputs = self.get_inputs()
        evaluators = self.get_evaluators()

        # Compute the reference once per input.
        expected_states = [
            self._reference_evaluator.evaluate(ins)
            for ins in inputs
        ]

        results = []

        for input_index, ins in enumerate(inputs):
            expected_state = expected_states[input_index]

            input_state = helper_qubits.get_system_state_from_qubits(ins)

            row = {
                "input_index": input_index,
                "input": helper_qubits.convert_state_to_amp_qet(input_state),
                "expected": helper_qubits.convert_state_to_amp_qet(
                    expected_state
                ),
            }

            all_passed = True

            for evaluator in evaluators:
                identifier = evaluator.get_identifier()
                actual_state = evaluator.evaluate(ins)

                passed = helper_qubits.compare_two_states(
                    actual_state,
                    expected_state,
                )

                row[f"state_{identifier}"] = (
                    helper_qubits.convert_state_to_amp_qet(actual_state)
                )
                row[f"comp_{identifier}_expected"] = passed

                all_passed = all_passed and passed

            row["comp_evaluator_all"] = all_passed
            results.append(row)

        return results