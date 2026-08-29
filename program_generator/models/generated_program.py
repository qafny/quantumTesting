from dataclasses import dataclass
from typing import Sequence

from qiskit import QuantumCircuit

from .generation_config import GenerationConfig


@dataclass
class GeneratedProgram:
    circuit: QuantumCircuit
    config: GenerationConfig
    original_ops: dict
    gate_sequence: list[dict]

    @property
    def sample_id(self) -> int:
        return self.config.sample_id

    @property
    def seed(self) -> int:
        return self.config.seed

    @property
    def num_qubits(self) -> int:
        return self.config.num_qubits

    @property
    def num_gates(self) -> int:
        return self.config.num_gates

    @property
    def generation_gates(self) -> Sequence[str]:
        return self.config.generation_gates