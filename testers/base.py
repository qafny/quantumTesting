from abc import ABC, abstractmethod
from qiskit import QuantumCircuit


class BaseTester(ABC):

    def __init__(self, qc: QuantumCircuit):
        self._qc = qc

    def get_circuit(self) -> QuantumCircuit:
        return self._qc

    '''
    Returns a unique identifier for the tester. This is used in the results
    '''
    @abstractmethod
    def get_identifier(self) -> str:
        pass

    '''
    Returns a descriptive text of the tester. For PBT, describe the property being tested.
    '''
    @abstractmethod
    def get_description(self) -> str:
        pass

    '''
    Returns True/False depending on whether the test succeeded. For PBT, return True if the circuit satisfies the property
    of interest, False otherwise.
    '''
    @abstractmethod
    def test(self, **kwargs) -> bool:
        pass
