import logging
from typing import List, Dict, Any, Tuple
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
import helpers.qubits as helper_qubits
from testers.base import BaseTester


class QuCheckPropertiesPairwiseComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]]):
        logging.info("Initializing QuCheckPropertiesPairwiseComparator")
        super(QuCheckPropertiesPairwiseComparator, self).__init__(evaluators, inputs)
        logging.info("Finished Initializing QuCheckPropertiesPairwiseComparator")

    @staticmethod
    def get_identifier() -> str:
        return "qcp"

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using QuCheckPropertiesPairwiseComparator")

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()

        outs = []
        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            out = {
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
            }

            states = []
            '''
            TODO:
                1. Add any lists to store other property-related data, to be populated in the following loop
            '''
            for eval_idx, evaluator in enumerate(evaluators):
                logging.info(f"Evaluating using ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins}")
                state = evaluator.evaluate(ins)
                states.append(state)
                out[f"state_evaluator_{eval_idx}_{evaluator.get_identifier()}"] = helper_qubits.convert_state_to_amp_qet(state)
                '''
                TODO: 
                    1. If there are any other properties to store, which are to be obtained through the evaluator, store
                    them here in a similar variable to states.
                    2. Add all such property related data to out variable as well.
                '''
                logging.info(f"Finished Evaluating using ({eval_idx}) {evaluator.get_identifier()}")

            # Pairwise comparison
            for i in range(len(evaluators)):
                for j in range(i + 1, len(evaluators)):
                    '''
                    TODO: 
                        1. Perform the properties pairwise comparison here. We currently store state[i] and state[j] for
                        the evaluator pair evaluators[i] and evaluators[j].
                        2. Add the results to out
                    '''
                    # TODO: Add the code here
                    pass

            # All comparison
            '''
            TODO: 
                1. Check whether, for all properties, the check passes (is equivalent) across all evaluators.
                2. Add the results to out
            '''
            # TODO: Add the code here

            outs.append(out)

        logging.info("Finished Comparing using QuCheckPropertiesPairwiseComparator")

        return outs


class QuCheckExpectedPropertiesComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]], testers: List[BaseTester]):
        logging.info("Initializing QuCheckExpectedPropertiesComparator")
        super(QuCheckExpectedPropertiesComparator, self).__init__(evaluators, inputs)
        self.testers: List[BaseTester] = testers
        logging.info("Finished Initializing QuCheckExpectedPropertiesComparator")

    @staticmethod
    def get_identifier() -> str:
        return "qcio"

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using QuCheckExpectedPropertiesComparator")

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()
        testers = self.testers

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

                # Running Testers
                logging.info(f"Running testers for evaluator ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins} and resulting state {state}")
                for tester_idx, tester in enumerate(testers):
                    logging.info(f"Running tester ({tester_idx}) {tester.get_identifier()} for description: {tester.get_description()}")
                    '''
                    TODO:
                        1. Pass any other information as required to the testers in general
                    '''
                    tester_result = tester.test(evaluator = evaluator, input = ins, state = state)
                    out[f"result_eval_{eval_idx}_{evaluator.get_identifier()}_tester_{tester_idx}_{tester.get_identifier()}"] = tester_result
                    logging.info(f"Finished Running tester ({tester_idx}) {tester.get_identifier()}")

                logging.info(f"Finished Running testers for evaluator ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins} and resulting state {state}")

            outs.append(out)

        logging.info("Finished Comparing using QuCheckExpectedPropertiesComparator")

        return outs
