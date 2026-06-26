
import math

from qiskit import QuantumCircuit

N_QUBITS = 3
X_VALUE = 1


def apply_qft(circuit: QuantumCircuit, qubits: list[int]) -> None:
    """
    Apply QFT to the given qubits.
    """
    n = len(qubits)

    for j in range(n):
        circuit.h(qubits[j])

        for k in range(j + 1, n):
            angle = math.pi / (2 ** (k - j))
            circuit.cp(angle, qubits[k], qubits[j])

    for i in range(n // 2):
        circuit.swap(qubits[i], qubits[n - i - 1])


def apply_inverse_qft(circuit: QuantumCircuit, qubits: list[int]) -> None:
    """
    Apply inverse QFT to the given qubits.
    """
    n = len(qubits)

    for i in range(n // 2):
        circuit.swap(qubits[i], qubits[n - i - 1])

    for j in reversed(range(n)):
        for k in reversed(range(j + 1, n)):
            angle = -math.pi / (2 ** (k - j))
            circuit.cp(angle, qubits[k], qubits[j])

        circuit.h(qubits[j])


def apply_qft_add_classical(
    circuit: QuantumCircuit,
    x_value: int,
    y_qubits: list[int]
) -> None:
    """
    Add a classical integer x_value into the quantum register y.

    Operation:
        |y> -> |y + x_value mod 2^n>
    """
    n = len(y_qubits)

    apply_qft(circuit, y_qubits)

    for i in range(n):
        angle = 2 * math.pi * x_value * (2 ** (i - n))
        circuit.p(angle, y_qubits[i])

    apply_inverse_qft(circuit, y_qubits)


qft_adder_circuit = QuantumCircuit(N_QUBITS, name="qft_adder_add_1")

apply_qft_add_classical(
    circuit=qft_adder_circuit,
    x_value=X_VALUE,
    y_qubits=list(range(N_QUBITS))
)