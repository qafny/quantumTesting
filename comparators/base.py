from abc import ABC, abstractmethod
from typing import Dict, List, Any
from evaluators.base import BaseEvaluator


class BaseComparator(ABC):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]]):
        self._evaluators: List[BaseEvaluator] = evaluators
        self._inputs: List[Dict[str, bool]] = inputs

    @staticmethod
    @abstractmethod
    def get_identifier() -> str:
        pass

    def add_evaluator(self, evaluator: BaseEvaluator):
        self._evaluators.append(evaluator)

    def get_evaluators(self) -> List[BaseEvaluator]:
        return self._evaluators

    def get_inputs(self) -> List[Dict[str, bool]]:
        return self._inputs

    @abstractmethod
    def compare(self) -> List[Dict[Any, Any]]:
        pass
