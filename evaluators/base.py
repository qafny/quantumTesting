from abc import ABC, abstractmethod

from parser.qiskit import QiskitASTParser
from qetast.nodes import QXRoot


class BaseEvaluator(ABC):

    def __init__(self):
        self._state = None

    def set_state(self, state):
        self._state = state

    def get_state(self):
        return self._state

    @abstractmethod
    def evaluate(self, *args, **kwargs):
        pass
