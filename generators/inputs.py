import random
from abc import ABC, abstractmethod
from typing import Dict, List
import helpers.qubits as helpers_qubits


class BaseInputGenerator(ABC):

    def __init__(self, qubits_count: int):
        self._qubits_count = qubits_count

    @staticmethod
    @abstractmethod
    def get_identifier() -> str:
        pass

    def get_qubits_count(self) -> int:
        return self._qubits_count

    @abstractmethod
    def generate(self) -> List[Dict[str, bool]]:
        pass


class CompleteInputSpaceGenerator(BaseInputGenerator):

    def __init__(self, qubits_count: int):
        super(CompleteInputSpaceGenerator, self).__init__(qubits_count)

    @staticmethod
    def get_identifier():
        return "cis"

    def generate(self) -> List[Dict[str, bool]]:
        qubit_states = []
        helpers_qubits.gen_qubit_states(qubit_states, [False] * self.get_qubits_count(), 0)

        ins = []
        for qubit_state in qubit_states:
            ins_state = {}
            for idx, qstate in enumerate(qubit_state):
                ins_state[str(idx)] = qstate

            ins.append(ins_state)

        return ins


class RandomInputGenerator(BaseInputGenerator):

    def __init__(self, qubits_count: int, ins_count: int):
        super(RandomInputGenerator, self).__init__(qubits_count)
        self._ins_count: int = ins_count

    @staticmethod
    def get_identifier():
        return "random"

    def generate(self) -> List[Dict[str, bool]]:
        ins = []
        for _ in range(self._ins_count):
            ins_state = {}
            for idx in range(self.get_qubits_count()):
                ins_state[str(idx)] = random.choice([True, False])

            ins.append(ins_state)

        return ins
