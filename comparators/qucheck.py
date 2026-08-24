import logging
from typing import List, Dict, Any, Tuple
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
import helpers.qubits as helper_qubits
from testers.base import BaseTester
import math
import numpy as np


def compute_marginal_probabilities(state: List[Tuple[complex, Dict[str, bool]]], qubit_idx: int) -> float:
    prob = 0.0
    for amp, sd in state:
        if sd.get(str(qubit_idx), False):
            prob += abs(amp) ** 2
    return prob


def compute_parity(state: List[Tuple[complex, Dict[str, bool]]]) -> float:
    even = 0.0
    odd = 0.0
    for amp, sd in state:
        parity = sum(1 for bit in sd.values() if bit) % 2
        if parity == 0:
            even += abs(amp) ** 2
        else:
            odd += abs(amp) ** 2
    return even - odd


def is_unitary_matrix(U: np.ndarray, tol: float = 1e-6) -> bool:
    n = U.shape[0]
    eye = np.eye(n, dtype=complex)
    UHU = U.conj().T @ U
    return np.allclose(UHU, eye, atol=tol)


def are_unitaries_equal(U1: np.ndarray, U2: np.ndarray, tol: float = 1e-6) -> bool:
    for i in range(U1.shape[0]):
        for j in range(U1.shape[1]):
            if abs(U1[i, j]) > tol and abs(U2[i, j]) > tol:
                phase = U1[i, j] / U2[i, j]
                phase = phase / abs(phase)
                return np.allclose(U1, phase * U2, atol=tol)
    return np.allclose(U1, U2, atol=tol)


def normalize_state(state: List[Tuple[complex, Dict[str, bool]]]) -> bool:
    total = sum(abs(amp) ** 2 for amp, _ in state)
    return math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6)


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

        unitaries = []
        for eval_idx, evaluator in enumerate(evaluators):
            U = evaluator.get_unitary()
            unitaries.append(U)
            logging.info(f"Computed unitary for evaluator {eval_idx} ({evaluator.get_identifier()})")

        outs = []
        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            out = {
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
            }
            
            '''
            TODO:
                1. Add any lists to store other property-related data, to be populated in the following loop
            '''
            all_states = []
            all_props = []
            n_qubits = None

            for eval_idx, evaluator in enumerate(evaluators):
                logging.info(f"Evaluating using ({eval_idx}) {evaluator.get_identifier()} on input ({ins_idx}) {ins}")
                state = evaluator.evaluate(ins)
                all_states.append(state)
                out[f"state_evaluator_{eval_idx}_{evaluator.get_identifier()}"] = helper_qubits.convert_state_to_amp_qet(state)
                '''
                TODO: 
                    1. If there are any other properties to store, which are to be obtained through the evaluator, store
                    them here in a similar variable to states.
                    2. Add all such property related data to out variable as well.
                '''

                if n_qubits is None and state:
                    n_qubits = len(next(iter(state))[1])
                if n_qubits is None:
                    n_qubits = 0

                props = {}

                props["is_normalized"] = normalize_state(state)

                for q in range(n_qubits):
                    props[f"prob_qubit_{q}"] = compute_marginal_probabilities(state, q)

                props["parity_expectation"] = compute_parity(state)

                prob_zero = sum(abs(a) ** 2 for a, sd in state if not any(sd.values()))
                prob_all_ones = sum(abs(a) ** 2 for a, sd in state if all(sd.values()))
                props["prob_zero"] = prob_zero
                props["prob_all_ones"] = prob_all_ones

                all_props.append(props)
                logging.info(f"Finished Evaluating using ({eval_idx}) {evaluator.get_identifier()}")

            for eval_idx, U in enumerate(unitaries):
                unitary_ok = is_unitary_matrix(U)
                out[f"is_unitary_evaluator_{eval_idx}_{evaluators[eval_idx].get_identifier()}"] = unitary_ok
                out[f"is_reversible_evaluator_{eval_idx}_{evaluators[eval_idx].get_identifier()}"] = unitary_ok

            if len(unitaries) > 1:
                all_unitaries_equal = True
                for i in range(len(unitaries)):
                    for j in range(i + 1, len(unitaries)):
                        eq = are_unitaries_equal(unitaries[i], unitaries[j])
                        out[f"unitary_comp_[evaluator_{i}_{evaluators[i].get_identifier()}]_[evaluator_{j}_{evaluators[j].get_identifier()}]"] = eq
                        if not eq:
                            all_unitaries_equal = False
                out["all_unitaries_equal"] = all_unitaries_equal
            else:
                out["all_unitaries_equal"] = True

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

                    props_i = all_props[i]
                    props_j = all_props[j]
                    equal = True
                    for key in props_i:
                        if key not in props_j:
                            equal = False
                            break
                        if not math.isclose(props_i[key], props_j[key], rel_tol=1e-6, abs_tol=1e-6):
                            equal = False
                            break
                    out[f"comp_[evaluator_{i}_{evaluators[i].get_identifier()}]_[evaluator_{j}_{evaluators[j].get_identifier()}]"] = equal

            # All comparison
            '''
            TODO: 
                1. Check whether, for all properties, the check passes (is equivalent) across all evaluators.
                2. Add the results to out
            '''
            # TODO: Add the code here

            all_equal = True
            if len(all_props) > 1:
                first_props = all_props[0]
                for props in all_props[1:]:
                    for key in first_props:
                        if key not in props or not math.isclose(first_props[key], props[key], rel_tol=1e-6, abs_tol=1e-6):
                            all_equal = False
                            break
                    if not all_equal:
                        break
            else:
                all_equal = True
            out["comp_evaluator_all"] = all_equal

            for idx, props in enumerate(all_props):
                out[f"properties_evaluator_{idx}_{evaluators[idx].get_identifier()}"] = props

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
