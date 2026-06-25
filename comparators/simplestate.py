import logging
from typing import List, Dict, Any, Tuple
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
import helpers.qubits as helper_qubits


class SimpleStatePairwiseComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]]):
        logging.info("Initializing SimpleStatePairwiseComparator")
        super(SimpleStatePairwiseComparator, self).__init__(evaluators, inputs)
        logging.info("Finished Initializing SimpleStatePairwiseComparator")

    @staticmethod
    def get_identifier() -> str:
        return "spa"

    @staticmethod
    def requires_expected_outputs() -> bool:
        return False

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using SimpleStatePairwiseComparator")

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()

        outs = []
        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            out = {
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
            }

            states = []
            for eval_idx, evaluator in enumerate(evaluators):
                logging.info(f"Evaluating using ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins}")
                state = evaluator.evaluate(ins)
                states.append(state)
                out[f"state_evaluator_{eval_idx}_{evaluator.get_identifier()}"] = helper_qubits.convert_state_to_amp_qet(state)
                logging.info(f"Finished Evaluating using ({eval_idx}) {evaluator.get_identifier()}")

            # Pairwise comparison
            for i in range(len(evaluators)):
                for j in range(i + 1, len(evaluators)):
                    out[f"comp_[evaluator_{i}_{evaluators[i].get_identifier()}]_[evaluator_{j}_{evaluators[j].get_identifier()}]"] = helper_qubits.compare_two_states(states[i], states[j])

            # All comparison
            out["comp_evaluator_all"] = all([helper_qubits.compare_two_states(state, states[0]) for state in states])

            outs.append(out)

        logging.info("Finished Comparing using SimpleStatePairwiseComparator")

        return outs


class SimpleStateExpectedOutputComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]], expected: List[Dict[str, bool]]):
        logging.info("Initializing SimpleStateInputOutputComparator")
        super(SimpleStateExpectedOutputComparator, self).__init__(evaluators, inputs)
        self.expected: List[Dict[str, bool]] = expected
        logging.info("Finished Initializing SimpleStateInputOutputComparator")

    @staticmethod
    def get_identifier() -> str:
        return "sio"

    @staticmethod
    def requires_expected_outputs() -> bool:
        return True

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using SimpleStateInputOutputComparator")

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()
        expected = self.expected

        outs = []
        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            expected_state: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(expected[ins_idx])
            out = {
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
                "expected": helper_qubits.convert_state_to_amp_qet(expected_state),
            }

            states = []
            for eval_idx, evaluator in enumerate(evaluators):
                logging.info(f"Evaluating using ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins}")
                state = evaluator.evaluate(ins)
                states.append(state)
                out[f"state_evaluator_{eval_idx}_{evaluator.get_identifier()}"] = helper_qubits.convert_state_to_amp_qet(state)
                logging.info(f"Finished Evaluating using ({eval_idx}) {evaluator.get_identifier()}")

                out[f"comp_[evaluator_{eval_idx}_{evaluators[eval_idx].get_identifier()}]_expected"] = helper_qubits.compare_two_states(state, expected_state)

            outs.append(out)

        logging.info("Finished Comparing using SimpleStateInputOutputComparator")

        return outs
