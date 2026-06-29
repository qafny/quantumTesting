from qiskit import QuantumCircuit, QuantumRegister


N_QUBITS = 3

# ---------------------------------------------------------------------
# These are cyclic shifts.
#
# lshift:
#   swaps from right to left:
#     swap(a[n-1], a[n-2])
#     swap(a[n-2], a[n-3])
#     ...
#
# rshift:
#   swaps from left to right:
#     swap(a[0], a[1])
#     swap(a[1], a[2])
#     ...
#
# Controlled versions use cswap.
# ---------------------------------------------------------------------

def lshift(circ, a, n=-1):
    """
    Cyclically left-shift a binary register.
    """
    if n == -1:
        n = len(a)

    for i in range(n, 1, -1):
        circ.swap(a[i - 1], a[i - 2])


def rshift(circ, a, n=-1):
    """
    Cyclically right-shift a binary register.
    """
    if n == -1:
        n = len(a)

    for i in range(n - 1):
        circ.swap(a[i], a[i + 1])


def c_lshift(circ, control, a, n=-1):
    """
    Controlled cyclic left shift.

    If control == 1, apply lshift.
    If control == 0, leave the register unchanged.
    """
    if n == -1:
        n = len(a)

    for i in range(n, 1, -1):
        circ.cswap(control, a[i - 1], a[i - 2])


def c_rshift(circ, control, a, n=-1):
    """
    Controlled cyclic right shift.

    If control == 1, apply rshift.
    If control == 0, leave the register unchanged.
    """
    if n == -1:
        n = len(a)

    for i in range(n - 1):
        circ.cswap(control, a[i], a[i + 1])


# ---------------------------------------------------------------------
# Circuit 1: qarithmetic_lshift
#
# Qubit layout:
#   a[0:3] = input/output register
#
# Total qubits = 3
# ---------------------------------------------------------------------

a_lshift = QuantumRegister(N_QUBITS, "a_lshift")

lshift_circuit = QuantumCircuit(
    a_lshift,
    name="lshift"
)

lshift(
    circ=lshift_circuit,
    a=list(a_lshift),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 2: qarithmetic_rshift
#
# Qubit layout:
#   a[0:3] = input/output register
#
# Total qubits = 3
# ---------------------------------------------------------------------

a_rshift = QuantumRegister(N_QUBITS, "a_rshift")

rshift_circuit = QuantumCircuit(
    a_rshift,
    name="rshift"
)

rshift(
    circ=rshift_circuit,
    a=list(a_rshift),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 3: qarithmetic_controlled_lshift
#
# Qubit layout:
#   control[0] = control qubit
#   a[0:3]     = input/output register
#
# Total qubits = 4
# ---------------------------------------------------------------------

control_lshift = QuantumRegister(1, "control_lshift")
a_controlled_lshift = QuantumRegister(N_QUBITS, "a_controlled_lshift")

controlled_lshift_circuit = QuantumCircuit(
    control_lshift,
    a_controlled_lshift,
    name="controlled_lshift"
)

c_lshift(
    circ=controlled_lshift_circuit,
    control=control_lshift[0],
    a=list(a_controlled_lshift),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 4: qarithmetic_controlled_rshift
#
# Qubit layout:
#   control[0] = control qubit
#   a[0:3]     = input/output register
#
# Total qubits = 4
# ---------------------------------------------------------------------

control_rshift = QuantumRegister(1, "control_rshift")
a_controlled_rshift = QuantumRegister(N_QUBITS, "a_controlled_rshift")

controlled_rshift_circuit = QuantumCircuit(
    control_rshift,
    a_controlled_rshift,
    name="controlled_rshift"
)

c_rshift(
    circ=controlled_rshift_circuit,
    control=control_rshift[0],
    a=list(a_controlled_rshift),
    n=N_QUBITS
)