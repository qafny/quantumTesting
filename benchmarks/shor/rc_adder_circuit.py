from qiskit import QuantumCircuit, QuantumRegister


N_QUBITS = 3
X_VALUE = 1


y = QuantumRegister(N_QUBITS, "y")
a = QuantumRegister(N_QUBITS + 1, "a")

rc_adder_circuit = QuantumCircuit(y, a, name="rc_adder_add_1")

def maj(circuit, qa, qb, qc):
    """

    MAJGate behavior:
        cx c, b
        cx c, a
        ccx a, b, c
    """
    circuit.cx(qc, qb)
    circuit.cx(qc, qa)
    circuit.ccx(qa, qb, qc)


def uma_rc(circuit, qa, qb, qc):
    """
    RC-version UMA behavior:
        x b
        cx a, b
        ccx a, b, c
        x b
        cx c, a
        cx c, b
    """
    circuit.x(qb)
    circuit.cx(qa, qb)
    circuit.ccx(qa, qb, qc)
    circuit.x(qb)
    circuit.cx(qc, qa)
    circuit.cx(qc, qb)


def encode_classical_value(circuit, x_value, x_qubits):
    """
    Encode classical integer X into the x_qubits register using X gates.

    This follows qiskit-shor's bitwise_AND_classical behavior when
    the target register starts in |0>.
    """
    n = len(x_qubits)
    x_mod = x_value % (2 ** n)

    for i in range(n):
        if (x_mod >> i) & 1:
            circuit.x(x_qubits[i])


def add_quantum_ripple_carry(circuit, x_qubits, y_qubits, ancilla_qubit):
    """
    Ripple-carry addition:

        |x>|y>|0> -> |x>|x + y>|0>

    """
    n = len(y_qubits)

    maj(circuit, ancilla_qubit, y_qubits[0], x_qubits[0])

    for i in range(n - 1):
        maj(circuit, x_qubits[i], y_qubits[i + 1], x_qubits[i + 1])

    for i in range(n - 1, 0, -1):
        uma_rc(circuit, x_qubits[i - 1], y_qubits[i], x_qubits[i])

    uma_rc(circuit, ancilla_qubit, y_qubits[0], x_qubits[0])


def add_classical_ripple_carry(circuit, x_value, y_qubits, ancilla_qubits):
    """
    Add a classical integer X into y:

        |y>|0...0> -> |y + X mod 2^n>|0...0>

    ancilla_qubits[0] is the carry ancilla.
    ancilla_qubits[1:] temporarily stores the classical X value.
    """
    n = len(y_qubits)

    carry_ancilla = ancilla_qubits[0]
    x_qubits = ancilla_qubits[1:n + 1]

    encode_classical_value(circuit, x_value, x_qubits)

    add_quantum_ripple_carry(
        circuit=circuit,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        ancilla_qubit=carry_ancilla
    )

    encode_classical_value(circuit, x_value, x_qubits)


add_classical_ripple_carry(
    circuit=rc_adder_circuit,
    x_value=X_VALUE,
    y_qubits=list(y),
    ancilla_qubits=list(a)
)