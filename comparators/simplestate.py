import logging
from typing import List, Dict, Any
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator


class SimpleStateComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]]):
        logging.info("Initializing SimpleStateComparator")
        super(SimpleStateComparator, self).__init__(evaluators, inputs)
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
            out = {
                "input": ins,
            }

            states = []
            for eval_idx, evaluator in enumerate(evaluators):
                logging.info(f"Evaluating using ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins}")
                state = evaluator.evaluate(ins)
                states.append(state)
                out[f"state_evaluator_{eval_idx}_{evaluator.get_identifier()}"] = state
                logging.info(f"Finished Evaluating using ({eval_idx}) {evaluator.get_identifier()}")

            # Pairwise comparison
            for i in range(len(evaluators)):
                for j in range(i + 1, len(evaluators)):
                    out[f"comp_[evaluator_{i}_{evaluators[i].get_identifier()}]_[evaluator_{j}_{evaluators[j].get_identifier()}]"] = states[i] == states[j]

            # All comparison
            out["comp_evaluator_all"] = all([state == states[0] for state in states])

            outs.append(out)

        logging.info("Finished Comparing using SimpleStateComparator")

        return outs
