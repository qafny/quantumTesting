from typing import List
from comparators.base import BaseComparator
from comparators.qucheck import QuCheckPropertiesPairwiseComparator, QuCheckExpectedPropertiesComparator
from comparators.simplestate import SimpleStatePairwiseComparator, SimpleStateExpectedOutputComparator
from evaluators.base import BaseEvaluator
from evaluators.qet import QETEvaluator
from evaluators.qucheck import QuCheckEvaluator
from evaluators.tsim import TSimEvaluator


def parse_comparator(comparator_id: str) -> type[BaseComparator]:
    if comparator_id == SimpleStatePairwiseComparator.get_identifier():
        return SimpleStatePairwiseComparator
    elif comparator_id == SimpleStateExpectedOutputComparator.get_identifier():
        return SimpleStateExpectedOutputComparator
    elif comparator_id == QuCheckPropertiesPairwiseComparator.get_identifier():
        return QuCheckPropertiesPairwiseComparator
    elif comparator_id == QuCheckExpectedPropertiesComparator.get_identifier():
        return QuCheckExpectedPropertiesComparator
    else:
        raise Exception(f"Unknown comparator {comparator_id}")


def parse_evaluators_list(evaluators_list: List[str]) -> List[type[BaseEvaluator]]:
    evals = []

    for evaluator_id in evaluators_list:
        if evaluator_id == QETEvaluator.get_identifier():
            evals.append(QETEvaluator)
        elif evaluator_id == TSimEvaluator.get_identifier():
            evals.append(TSimEvaluator)
        elif evaluator_id == QuCheckEvaluator.get_identifier():
            evals.append(QuCheckEvaluator)
        else:
            raise Exception(f"Unknown evaluator {evaluator_id}")

    return evals
