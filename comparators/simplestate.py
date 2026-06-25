import logging
from typing import List, Dict, Any, Tuple
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
import helpers.qubits as helper_qubits


class SimpleStatePairwiseComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]]):
        logging.info("Initializing SimpleStateComparator")
        super(SimpleStatePairwiseComparator, self).__init__(evaluators, inputs)
        logging.info("Finished Initializing SimpleStateComparator")

    @staticmethod
    def get_identifier() -> str:
        return "spa"

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using SimpleStateComparator")

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

        logging.info("Finished Comparing using SimpleStateComparator")

        return outs
