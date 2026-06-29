from qiskit import QuantumCircuit, QuantumRegister


N_QUBITS = 3
X_VALUE = 1


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


def inv_maj(circuit, qa, qb, qc):
    """
    Inverse of maj().
    Since cx and ccx are self-inverse, we apply the gates in reverse order.
    """
    circuit.ccx(qa, qb, qc)
    circuit.cx(qc, qa)
    circuit.cx(qc, qb)


def uma_rc(circuit, qa, qb, qc):
    """
    Unmajority-and-add behavior:
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


def inv_uma_rc(circuit, qa, qb, qc):
    """
    Inverse of uma_rc().
    Gates are applied in reverse order.
    """
    circuit.cx(qc, qb)
    circuit.cx(qc, qa)
    circuit.x(qb)
    circuit.ccx(qa, qb, qc)
    circuit.cx(qa, qb)
    circuit.x(qb)


def encode_classical_value(circuit, x_value, x_qubits):
    """
    Encode a classical integer into a temporary quantum register using X gates.

    Example:
        x_value = 1
        x_qubits = [q0, q1, q2]

    Then q0 is flipped because 1 = 001.
    """
    n = len(x_qubits)
    x_mod = x_value % (2 ** n)

    for i in range(n):
        if (x_mod >> i) & 1:
            circuit.x(x_qubits[i])


def add_quantum_ripple_carry(circuit, x_qubits, y_qubits, carry_ancilla):
    """
    Ripple-carry addition.

    Operation:
        |x>|y>|0> -> |x>|x + y mod 2^n>|0>

    x_qubits are preserved.
    y_qubits store the result.
    carry_ancilla must start as |0>.
    """
    n = len(y_qubits)

    maj(circuit, carry_ancilla, y_qubits[0], x_qubits[0])

    for i in range(n - 1):
        maj(circuit, x_qubits[i], y_qubits[i + 1], x_qubits[i + 1])

    for i in range(n - 1, 0, -1):
        uma_rc(circuit, x_qubits[i - 1], y_qubits[i], x_qubits[i])

    uma_rc(circuit, carry_ancilla, y_qubits[0], x_qubits[0])


def subtract_quantum_ripple_carry(circuit, x_qubits, y_qubits, carry_ancilla):
    """
    Inverse of add_quantum_ripple_carry.

    Operation:
        |x>|y>|0> -> |x>|y - x mod 2^n>|0>
    """
    n = len(y_qubits)

    inv_uma_rc(circuit, carry_ancilla, y_qubits[0], x_qubits[0])

    for i in range(1, n):
        inv_uma_rc(circuit, x_qubits[i - 1], y_qubits[i], x_qubits[i])

    for i in range(n - 2, -1, -1):
        inv_maj(circuit, x_qubits[i], y_qubits[i + 1], x_qubits[i + 1])

    inv_maj(circuit, carry_ancilla, y_qubits[0], x_qubits[0])


def add_classical_ripple_carry(circuit, x_value, y_qubits, ancilla_qubits):
    """
    Add a fixed classical integer into y.

    Operation:
        |y>|0...0> -> |y + x_value mod 2^n>|0...0>

    ancilla_qubits[0] is the carry ancilla.
    ancilla_qubits[1:] temporarily stores x_value.
    """
    n = len(y_qubits)

    carry_ancilla = ancilla_qubits[0]
    x_qubits = ancilla_qubits[1:n + 1]

    encode_classical_value(circuit, x_value, x_qubits)

    add_quantum_ripple_carry(
        circuit=circuit,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        carry_ancilla=carry_ancilla
    )

    encode_classical_value(circuit, x_value, x_qubits)


def subtract_classical_ripple_carry(circuit, x_value, y_qubits, ancilla_qubits):
    """
    Subtract a fixed classical integer from y.

    Operation:
        |y>|0...0> -> |y - x_value mod 2^n>|0...0>
    """
    n = len(y_qubits)

    carry_ancilla = ancilla_qubits[0]
    x_qubits = ancilla_qubits[1:n + 1]

    encode_classical_value(circuit, x_value, x_qubits)

    subtract_quantum_ripple_carry(
        circuit=circuit,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        carry_ancilla=carry_ancilla
    )

    encode_classical_value(circuit, x_value, x_qubits)


# ---------------------------------------------------------------------
# Circuit 1: rc_adder_add_classical
# Qubit layout:
#   y[0:3] = input register
#   a[0]   = carry ancilla
#   a[1:4] = temporary x register
# Total qubits = 7
# ---------------------------------------------------------------------

y_add_classical = QuantumRegister(N_QUBITS, "y")
a_add_classical = QuantumRegister(N_QUBITS + 1, "a")

rc_adder_add_classical_circuit = QuantumCircuit(
    y_add_classical,
    a_add_classical,
    name="rc_adder_add_classical"
)

add_classical_ripple_carry(
    circuit=rc_adder_add_classical_circuit,
    x_value=X_VALUE,
    y_qubits=list(y_add_classical),
    ancilla_qubits=list(a_add_classical)
)


# ---------------------------------------------------------------------
# Circuit 2: rc_adder_add_quantum
# Qubit layout:
#   x[0:3] = first input register
#   y[0:3] = second input/result register
#   c[0]   = carry ancilla
# Total qubits = 7
# ---------------------------------------------------------------------

x_add_quantum = QuantumRegister(N_QUBITS, "x")
y_add_quantum = QuantumRegister(N_QUBITS, "y")
c_add_quantum = QuantumRegister(1, "c")

rc_adder_add_quantum_circuit = QuantumCircuit(
    x_add_quantum,
    y_add_quantum,
    c_add_quantum,
    name="rc_adder_add_quantum"
)

add_quantum_ripple_carry(
    circuit=rc_adder_add_quantum_circuit,
    x_qubits=list(x_add_quantum),
    y_qubits=list(y_add_quantum),
    carry_ancilla=c_add_quantum[0]
)


# ---------------------------------------------------------------------
# Circuit 3: rc_adder_subtract_classical
# Qubit layout:
#   y[0:3] = input register
#   a[0]   = carry ancilla
#   a[1:4] = temporary x register
# Total qubits = 7
# ---------------------------------------------------------------------

y_subtract_classical = QuantumRegister(N_QUBITS, "y")
a_subtract_classical = QuantumRegister(N_QUBITS + 1, "a")

rc_adder_subtract_classical_circuit = QuantumCircuit(
    y_subtract_classical,
    a_subtract_classical,
    name="rc_adder_subtract_classical"
)

subtract_classical_ripple_carry(
    circuit=rc_adder_subtract_classical_circuit,
    x_value=X_VALUE,
    y_qubits=list(y_subtract_classical),
    ancilla_qubits=list(a_subtract_classical)
)


# ---------------------------------------------------------------------
# Circuit 4: rc_adder_subtract_quantum
# Qubit layout:
#   x[0:3] = first input register
#   y[0:3] = second input/result register
#   c[0]   = carry ancilla
# Total qubits = 7
# ---------------------------------------------------------------------

x_subtract_quantum = QuantumRegister(N_QUBITS, "x")
y_subtract_quantum = QuantumRegister(N_QUBITS, "y")
c_subtract_quantum = QuantumRegister(1, "c")

rc_adder_subtract_quantum_circuit = QuantumCircuit(
    x_subtract_quantum,
    y_subtract_quantum,
    c_subtract_quantum,
    name="rc_adder_subtract_quantum"
)

subtract_quantum_ripple_carry(
    circuit=rc_adder_subtract_quantum_circuit,
    x_qubits=list(x_subtract_quantum),
    y_qubits=list(y_subtract_quantum),
    carry_ancilla=c_subtract_quantum[0]
)