from qiskit import QuantumCircuit

from helpers.qiskit import transpile_qiskit_circuit
from evaluators.basis import QETGateSetBasis
from qiskit import transpile

def run_transpiler(
    circuit: QuantumCircuit,
    basis_gates: list[str] | None = None,
) -> QuantumCircuit:
    # return transpile(circuit, optimization_level=0)
    return transpile_qiskit_circuit(
        circuit,
        basis =QETGateSetBasis(),
        optimization_level=2
    )