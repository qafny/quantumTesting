from qiskit import QuantumCircuit, QuantumRegister

N_QUBITS = 3

# Assumption:
#   Output register c starts as all |0>.

def bitwise_and(qc, a, b, c, n):
    """
    Bitwise AND.

    Operation:
        |a>|b>|0> -> |a>|b>|a AND b>
    """
    for i in range(n):
        qc.ccx(a[i], b[i], c[i])


def bitwise_or(qc, a, b, c, n):
    """
    Bitwise OR.

    Operation:
        |a>|b>|0> -> |a>|b>|a OR b>

    Logic:
        c = ab XOR a XOR b
        This equals OR when c starts at 0.
    """
    for i in range(n):
        qc.ccx(a[i], b[i], c[i])
        qc.cx(a[i], c[i])
        qc.cx(b[i], c[i])


def bitwise_xor(qc, a, b, c, n):
    """
    Bitwise XOR.

    Operation:
        |a>|b>|0> -> |a>|b>|a XOR b>
    """
    for i in range(n):
        qc.cx(a[i], c[i])
        qc.cx(b[i], c[i])


def bitwise_not(qc, a, c, n):
    """
    Bitwise NOT.

    Operation:
        |a>|0> -> |a>|NOT a>
    """
    for i in range(n):
        qc.cx(a[i], c[i])
        qc.x(c[i])


# ---------------------------------------------------------------------
# Circuit 1: bitwise_and
# Qubit layout:
#   a[0:3] = first input register
#   b[0:3] = second input register
#   c[0:3] = output register, must start as 0
#
# Total qubits = 9
# ---------------------------------------------------------------------

a_and = QuantumRegister(N_QUBITS, "a_and")
b_and = QuantumRegister(N_QUBITS, "b_and")
c_and = QuantumRegister(N_QUBITS, "c_and")

qarithmetic_bitwise_and_circuit = QuantumCircuit(
    a_and,
    b_and,
    c_and,
    name="bitwise_and"
)

bitwise_and(
    qc=qarithmetic_bitwise_and_circuit,
    a=list(a_and),
    b=list(b_and),
    c=list(c_and),
    n=N_QUBITS
)

# ---------------------------------------------------------------------
# Circuit 2: qarithmetic_bitwise_or
# Qubit layout:
#   a[0:3] = first input register
#   b[0:3] = second input register
#   c[0:3] = output register, must start as 0
#
# Total qubits = 9
# ---------------------------------------------------------------------

a_or = QuantumRegister(N_QUBITS, "a_or")
b_or = QuantumRegister(N_QUBITS, "b_or")
c_or = QuantumRegister(N_QUBITS, "c_or")

qarithmetic_bitwise_or_circuit = QuantumCircuit(
    a_or,
    b_or,
    c_or,
    name="bitwise_or"
)

bitwise_or(
    qc=qarithmetic_bitwise_or_circuit,
    a=list(a_or),
    b=list(b_or),
    c=list(c_or),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 3: qarithmetic_bitwise_xor
#
# Qubit layout:
#   a[0:3] = first input register
#   b[0:3] = second input register
#   c[0:3] = output register, must start as 0
#
# Total qubits = 9
# ---------------------------------------------------------------------

a_xor = QuantumRegister(N_QUBITS, "a_xor")
b_xor = QuantumRegister(N_QUBITS, "b_xor")
c_xor = QuantumRegister(N_QUBITS, "c_xor")

qarithmetic_bitwise_xor_circuit = QuantumCircuit(
    a_xor,
    b_xor,
    c_xor,
    name="bitwise_xor"
)

bitwise_xor(
    qc=qarithmetic_bitwise_xor_circuit,
    a=list(a_xor),
    b=list(b_xor),
    c=list(c_xor),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 4: qarithmetic_bitwise_not
#
# Qubit layout:
#   a[0:3] = input register
#   c[0:3] = output register, must start as 0
#
# Total qubits = 6
# ---------------------------------------------------------------------

a_not = QuantumRegister(N_QUBITS, "a_not")
c_not = QuantumRegister(N_QUBITS, "c_not")

qarithmetic_bitwise_not_circuit = QuantumCircuit(
    a_not,
    c_not,
    name="bitwise_not"
)

bitwise_not(
    qc=qarithmetic_bitwise_not_circuit,
    a=list(a_not),
    c=list(c_not),
    n=N_QUBITS
)