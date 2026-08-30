from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BasisSet:
    name: str
    exact_gates: set[str]
    allow_controlled_unitary: bool = False
    controlled_gate_names: set[str] | None = None

    def is_allowed(self, gate_name: str) -> bool:
        gate_name = gate_name.lower()

        if gate_name in self.exact_gates:
            return True

        if self.allow_controlled_unitary:
            controlled_names = self.controlled_gate_names or set()
            return gate_name in controlled_names

        return False


@dataclass
class BasisCheckResult:
    passed: bool
    unexpected_ops: set[str]
    transpiled_ops: dict[str, int]


@dataclass
class EquivalenceCheckResult:
    passed: bool
    reason: str


@dataclass
class TranspilerTestResult:
    sample_id: int
    seed: int
    num_qubits: int
    num_gates: int
    generation_gates: list[str]
    basis_set_name: str

    original_ops: dict[str, int]
    transpiled_ops: dict[str, int]

    basis_passed: bool
    equivalence_passed: bool
    unexpected_ops: set[str]
    equivalence_reason: str

    @property
    def passed(self) -> bool:
        return self.basis_passed and self.equivalence_passed

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"