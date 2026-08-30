from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from compiler_testing.reporting.result_models import EquivalenceCheckResult


def check_equivalence(
    original: QuantumCircuit,
    transformed: QuantumCircuit,
    atol: float = 1e-8,
) -> EquivalenceCheckResult:
    if original.num_qubits != transformed.num_qubits:
        return EquivalenceCheckResult(
            passed=False,
            reason=(
                f"qubit count mismatch: "
                f"original={original.num_qubits}, transformed={transformed.num_qubits}"
            ),
        )

    try:
        original_op = Operator(original)
        transformed_op = Operator(transformed)
    except Exception as exc:
        return EquivalenceCheckResult(
            passed=False,
            reason=f"failed to construct Operator: {exc}",
        )

    try:
        passed = original_op.equiv(transformed_op, atol=atol)
    except Exception as exc:
        return EquivalenceCheckResult(
            passed=False,
            reason=f"operator equivalence check failed: {exc}",
        )

    if passed:
        return EquivalenceCheckResult(
            passed=True,
            reason="operator equivalent",
        )

    return EquivalenceCheckResult(
        passed=False,
        reason="operator mismatch",
    )