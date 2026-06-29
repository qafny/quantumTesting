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

class BoundedRandomInputGenerator(BaseInputGenerator):
    """
    Generates random inputs where only selected register ranges are randomized. 
    Useful for circuits with helper/ancilla qubits.

    Example use case:
        total qubits = 13
        x register:
            qubits 0, 1, 2
            valid values 0 to 4
        y register:
            qubits 3, 4, 5
            valid values 0 to 4
        helper qubits:
            qubits 6 to 12
            always False
    """

    def __init__(self, qubits_count: int, ins_count: int, bounds: List[Dict]):
        super(BoundedRandomInputGenerator, self).__init__(qubits_count)
        self._ins_count: int = ins_count
        self._bounds: List[Dict] = bounds

        self._validate_bounds()

    @staticmethod
    def get_identifier():
        return "bounded_random"

    def _validate_bounds(self):
        """
        Validate the bounds configuration before generating inputs.

        Each bound dictionary must contain:
            start
            size
            min_value
            max_value
        """
        used_qubits = set()

        for bound in self._bounds:
            required_keys = ["start", "size", "min_value", "max_value"]

            for key in required_keys:
                if key not in bound:
                    raise ValueError(f"Missing required key '{key}' in bound config: {bound}")

            start = bound["start"]
            size = bound["size"]
            min_value = bound["min_value"]
            max_value = bound["max_value"]

            if not isinstance(start, int):
                raise ValueError(f"'start' must be an int: {bound}")

            if not isinstance(size, int):
                raise ValueError(f"'size' must be an int: {bound}")

            if not isinstance(min_value, int):
                raise ValueError(f"'min_value' must be an int: {bound}")

            if not isinstance(max_value, int):
                raise ValueError(f"'max_value' must be an int: {bound}")

            if start < 0:
                raise ValueError(f"'start' cannot be negative: {bound}")

            if size <= 0:
                raise ValueError(f"'size' must be greater than 0: {bound}")

            if start + size > self.get_qubits_count():
                raise ValueError(
                    f"Bound range exceeds qubits_count. "
                    f"start={start}, size={size}, qubits_count={self.get_qubits_count()}"
                )

            if min_value < 0:
                raise ValueError(f"'min_value' cannot be negative: {bound}")

            if max_value < min_value:
                raise ValueError(f"'max_value' cannot be less than 'min_value': {bound}")

            max_representable_value = (2 ** size) - 1

            if max_value > max_representable_value:
                raise ValueError(
                    f"'max_value'={max_value} cannot be represented with size={size} qubits. "
                    f"Maximum representable value is {max_representable_value}."
                )

            for qubit_idx in range(start, start + size):
                if qubit_idx in used_qubits:
                    raise ValueError(f"Overlapping bounded qubit range detected at qubit {qubit_idx}")

                used_qubits.add(qubit_idx)

    def _write_integer_to_state(
        self,
        ins_state: Dict[str, bool],
        value: int,
        start: int,
        size: int
    ):
        """
        Write integer value into ins_state using little-endian bit order.

        Example:
            value = 5
            binary = 101

            start = 3
            size = 3

            qubit 3 = True
            qubit 4 = False
            qubit 5 = True
        """
        for offset in range(size):
            bit_value = (value >> offset) & 1
            ins_state[str(start + offset)] = bool(bit_value)

    def generate(self) -> List[Dict[str, bool]]:
        ins = []

        for _ in range(self._ins_count):
            # Start with every qubit initialized to False.
            # This keeps helper/ancilla qubits clean by default.
            ins_state = {}

            for idx in range(self.get_qubits_count()):
                ins_state[str(idx)] = False

            # Randomize only the configured bounded registers.
            for bound in self._bounds:
                start = bound["start"]
                size = bound["size"]
                min_value = bound["min_value"]
                max_value = bound["max_value"]

                random_value = random.randint(min_value, max_value)
                self._write_integer_to_state(
                    ins_state=ins_state,
                    value=random_value,
                    start=start,
                    size=size
                )
            ins.append(ins_state)
        return ins
