from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class GenerationConfig:
    num_qubits: int
    num_gates: int
    generation_gates: Sequence[str]
    seed: int
    sample_id: int = 0

    def validate(self) -> None:
        if self.num_qubits <= 0:
            raise ValueError("num_qubits must be greater than 0")

        if self.num_gates <= 0:
            raise ValueError("num_gates must be greater than 0")

        if not self.generation_gates:
            raise ValueError("generation_gates cannot be empty")