from qiskit import QuantumCircuit

from compiler_testing.reporting.result_models import BasisCheckResult, BasisSet


def get_ops(circuit: QuantumCircuit) -> dict[str, int]:
    return dict(circuit.count_ops())


def check_basis(
    circuit: QuantumCircuit,
    basis_set: BasisSet,
) -> BasisCheckResult:
    ops = get_ops(circuit)

    unexpected_ops = {
        op_name
        for op_name in ops
        if not basis_set.is_allowed(op_name)
    }

    return BasisCheckResult(
        passed=len(unexpected_ops) == 0,
        unexpected_ops=unexpected_ops,
        transpiled_ops=ops,
    )