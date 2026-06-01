from abc import ABC, abstractmethod
from qetast.nodes import QXRoot


class BaseEvaluator(ABC):

    @abstractmethod
    def evaluate(self, root: QXRoot, *args, **kwargs):
        pass
