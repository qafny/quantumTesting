from typing import List, Dict
from qiskit import QuantumCircuit

from comparators.base import BaseComparator
from comparators.simplestate import SimpleStatePairwiseComparator
from evaluators.base import BaseEvaluator
from evaluators.qet import QETEvaluator
from evaluators.tsim import TSimEvaluator


def parse_comparator(comparator_id: str) -> type[BaseComparator]:
    if comparator_id == SimpleStatePairwiseComparator.get_identifier():
        return SimpleStatePairwiseComparator
    else:
        raise Exception(f"Unknown comparator {comparator_id}")


def parse_evaluators_list(evaluators_list: List[str]) -> List[type[BaseEvaluator]]:
    evals = []

    for evaluator_id in evaluators_list:
        if evaluator_id == QETEvaluator.get_identifier():
            evals.append(QETEvaluator)
        elif evaluator_id == TSimEvaluator.get_identifier():
            evals.append(TSimEvaluator)
        else:
            raise Exception(f"Unknown evaluator {evaluator_id}")

    return evals
