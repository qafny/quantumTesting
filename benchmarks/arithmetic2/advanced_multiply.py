from math import pi

from qiskit import QuantumCircuit, QuantumRegister


# ---------------------------------------------------------------------
# Change this value to scale all four circuits.
#
#   total qubits for multiply               = 4n
#   total qubits for controlled multiply    = 4n
#   total qubits for square                 = 3n
#   total qubits for divide                 = 5n
# ---------------------------------------------------------------------
N_QUBITS = 2


# ---------------------------------------------------------------------
# register helpers
# ---------------------------------------------------------------------

def sub_qr(qr, start, end):
    """
    Return qubits qr[start] through qr[end], inclusive.
    """
    return [qr[i] for i in range(start, end + 1)]


def full_qr(qr):
    """
    Return all qubits in a register/list.
    """
    return sub_qr(qr, 0, len(qr) - 1)


def apply_x_to_register(circ, register):
    """
    Apply X to every qubit in a register/list.
    """
    for qubit in register:
        circ.x(qubit)


# ---------------------------------------------------------------------
# QFT helpers

def qft(circ, q, n):
    """
    Quantum Fourier Transform on q[0:n].
    """
    for i in range(n, 0, -1):
        circ.h(q[i - 1])

        for j in range(i - 1, 0, -1):
            circ.cp(
                2 * pi / (2 ** (i - j + 1)),
                q[j - 1],
                q[i - 1]
            )


def iqft(circ, q, n):
    """
    Inverse Quantum Fourier Transform on q[0:n].
    """
    for i in range(1, n + 1):
        for j in range(1, i):
            circ.cp(
                -2 * pi / (2 ** (i - j + 1)),
                q[j - 1],
                q[i - 1]
            )

        circ.h(q[i - 1])


def ccu1(circ, theta, control_1, control_2, target):
    """
    Controlled-controlled phase rotation helper.

    This decomposes a doubly-controlled phase into cp/cx/cp/cx/cp.
    """
    circ.cp(theta / 2, control_2, target)
    circ.cx(control_1, control_2)
    circ.cp(-theta / 2, control_2, target)
    circ.cx(control_1, control_2)
    circ.cp(theta / 2, control_1, target)


def cqft(circ, control, q, n):
    """
    Controlled QFT on q[0:n].
    """
    for i in range(n, 0, -1):
        circ.ch(control, q[i - 1])

        for j in range(i - 1, 0, -1):
            ccu1(
                circ,
                2 * pi / (2 ** (i - j + 1)),
                control,
                q[j - 1],
                q[i - 1]
            )


def ciqft(circ, control, q, n):
    """
    Controlled inverse QFT on q[0:n].
    """
    for i in range(1, n + 1):
        for j in range(1, i):
            ccu1(
                circ,
                -2 * pi / (2 ** (i - j + 1)),
                control,
                q[j - 1],
                q[i - 1]
            )

        circ.ch(control, q[i - 1])


def add(circ, a, b, n):
    """
    Draper/QFT adder.

    Operation:
        |a>|b> -> |a>|a + b>

    a has length <= n.
    b has length n + 1.
    """
    n += 1

    qft(circ, b, n)

    for i in range(n, 0, -1):
        for j in range(i, 0, -1):
            if len(a) - 1 >= j - 1:
                circ.cp(
                    2 * pi / (2 ** (i - j + 1)),
                    a[j - 1],
                    b[i - 1]
                )

    iqft(circ, b, n)


def cadd(circ, control, a, b, n):
    """
    Controlled Draper/QFT adder.

    Operation:
        if control == 1:
            |a>|b> -> |a>|a + b>
    """
    n += 1

    cqft(circ, control, b, n)

    for i in range(n, 0, -1):
        for j in range(i, 0, -1):
            if len(a) - 1 >= j - 1:
                ccu1(
                    circ,
                    2 * pi / (2 ** (i - j + 1)),
                    control,
                    a[j - 1],
                    b[i - 1]
                )

    ciqft(circ, control, b, n)


def sub_swap(circ, a, b, n):
    """
    Operation:
        |a>|b> -> |a - b>|b>

    a and b have length n + 1.
    """
    apply_x_to_register(circ, a)
    add(circ, b, a, n - 1)
    apply_x_to_register(circ, a)


def lshift(circ, a, n=-1):
    """
    Cyclically left-shift a register.
    """
    if n == -1:
        n = len(a)

    for i in range(n, 1, -1):
        circ.swap(a[i - 1], a[i - 2])


# ---------------------------------------------------------------------
# Multiplication

def mult(circ, a, b, c, n):
    """
    Compute c = a * b.

    Registers:
        a length n
        b length n
        c length 2n, initially zero

    Operation:
        |a>|b>|0> -> |a>|b>|a*b>
    """
    for i in range(0, n):
        cadd(
            circ,
            a[i],
            b,
            sub_qr(c, i, n + i),
            n
        )


def cmult(circ, control, a, b, c, n):
    """
    Controlled multiplication.

    If control == 1:
        c = a * b

    If control == 0:
        c remains zero

    converting it into a controlled operation, and composing it back.
    """
    qa = QuantumRegister(len(a), "tmp_a")
    qb = QuantumRegister(len(b), "tmp_b")
    qc = QuantumRegister(len(c), "tmp_c")

    temp_circuit = QuantumCircuit(qa, qb, qc, name="tmp_mult")
    mult(temp_circuit, qa, qb, qc, n)

    controlled_mult_gate = temp_circuit.to_gate(label="controlled_mult").control(1)

    circ.append(
        controlled_mult_gate,
        [control] + list(a) + list(b) + list(c)
    )


# ---------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------

def div(circ, p, d, q, n):
    """

    Registers:
        p length 2n
        d length 2n
        q length n, initially zero

    Expected input convention:
        p contains the dividend in its lower n qubits.
        d contains the divisor shifted into its upper n qubits.
        q starts as zero.

    Operation:
        q receives quotient.
        upper part of p receives remainder information.
    """
    for i in range(n, 0, -1):
        # Left shift p.
        lshift(circ, p, 2 * n)

        # Subtract d from p.
        sub_swap(circ, p, d, 2 * n)

        # If p is positive, set quotient bit.
        circ.x(p[2 * n - 1])
        circ.cx(p[2 * n - 1], q[i - 1])
        circ.x(p[2 * n - 1])

        # If quotient bit was not set, add d back to p.
        circ.x(q[i - 1])
        cadd(circ, q[i - 1], d, p, 2 * n - 1)
        circ.x(q[i - 1])


# ---------------------------------------------------------------------
# Square

def square(circ, a, b, n=-1):
    """
    Compute b = a^2.

    Registers:
        a length n
        b length 2n, initially zero

    Operation:
        |a>|0> -> |a>|a^2>
    """
    if n == -1:
        n = len(a)

    # First addition.
    circ.cx(a[0], b[0])

    for i in range(1, n):
        circ.ccx(a[0], a[i], b[i])

    # Controlled QFT-based additions for remaining bits.
    for k in range(1, n):
        d = b[k:n + k + 1]

        qft(circ, d, n + 1)

        for i in range(n + 1, 0, -1):
            for j in range(i, 0, -1):
                if len(a) - 1 < j - 1:
                    continue

                if k == j - 1:
                    circ.cp(
                        2 * pi / (2 ** (i - j + 1)),
                        a[j - 1],
                        d[i - 1]
                    )
                else:
                    ccu1(
                        circ,
                        2 * pi / (2 ** (i - j + 1)),
                        a[k],
                        a[j - 1],
                        d[i - 1]
                    )

        iqft(circ, d, n + 1)


# ---------------------------------------------------------------------
# Circuit 1: multiply
#
# Qubit layout:
#   a[0:n]     = first input
#   b[0:n]     = second input
#   c[0:2n]    = product output, starts zero
#
# Total qubits = 4n
# ---------------------------------------------------------------------

a_mult = QuantumRegister(N_QUBITS, "a_mult")
b_mult = QuantumRegister(N_QUBITS, "b_mult")
c_mult = QuantumRegister(2 * N_QUBITS, "c_mult")

multiply_circuit = QuantumCircuit(
    a_mult,
    b_mult,
    c_mult,
    name="multiply"
)

mult(
    circ=multiply_circuit,
    a=list(a_mult),
    b=list(b_mult),
    c=list(c_mult),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 2: controlled_multiply
#
# Qubit layout:
#   control[0] = control qubit
#   a[0:n]     = first input
#   b[0:n]     = second input
#   c[0:2n]    = product output, starts zero
#
# Total qubits = 4n + 1
# ---------------------------------------------------------------------

control_cmult = QuantumRegister(1, "control_cmult")
a_cmult = QuantumRegister(N_QUBITS, "a_cmult")
b_cmult = QuantumRegister(N_QUBITS, "b_cmult")
c_cmult = QuantumRegister(2 * N_QUBITS, "c_cmult")

controlled_multiply_circuit = QuantumCircuit(
    control_cmult,
    a_cmult,
    b_cmult,
    c_cmult,
    name="controlled_multiply"
)

cmult(
    circ=controlled_multiply_circuit,
    control=control_cmult[0],
    a=list(a_cmult),
    b=list(b_cmult),
    c=list(c_cmult),
    n=N_QUBITS
)

# Decompose controlled custom multiplication gate so QET sees
# lower-level Qiskit operations.
controlled_multiply_circuit = (
    controlled_multiply_circuit.decompose(reps=10)
)


# ---------------------------------------------------------------------
# Circuit 3: square
#
# Qubit layout:
#   a[0:n]     = input
#   b[0:2n]    = square output, starts zero
#
# Total qubits = 3n
# ---------------------------------------------------------------------

a_square = QuantumRegister(N_QUBITS, "a_square")
b_square = QuantumRegister(2 * N_QUBITS, "b_square")

square_circuit = QuantumCircuit(
    a_square,
    b_square,
    name="square"
)

square(
    circ=square_circuit,
    a=list(a_square),
    b=list(b_square),
    n=N_QUBITS
)


# ---------------------------------------------------------------------
# Circuit 4: divide
#
# Qubit layout:
#   p[0:2n] = dividend/work register
#   d[0:2n] = divisor register, divisor is stored in upper n bits
#   q[0:n]  = quotient output, starts zero
#
# Total qubits = 5n
#
# Input convention for QET:
#   p lower n bits are randomized.
#   d upper n bits are randomized with nonzero divisor values.
#   all other p/d/q bits start zero.
# ---------------------------------------------------------------------

p_div = QuantumRegister(2 * N_QUBITS, "p_div")
d_div = QuantumRegister(2 * N_QUBITS, "d_div")
q_div = QuantumRegister(N_QUBITS, "q_div")

divide_circuit = QuantumCircuit(
    p_div,
    d_div,
    q_div,
    name="divide"
)

div(
    circ=divide_circuit,
    p=list(p_div),
    d=list(d_div),
    q=list(q_div),
    n=N_QUBITS
)