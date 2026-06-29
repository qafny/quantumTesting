import math

from qiskit import QuantumCircuit, QuantumRegister


# ---------------------------------------------------------------------
#
# Current benchmark:
#   MODULUS = 5
#   X_VALUE = 2
#
# Classical modular add:
#   |y> -> |(y + 2) mod 5>
#
# Classical modular subtract:
#   |y> -> |(y - 2) mod 5>
#
# Quantum modular add:
#   |x>|y> -> |x>|(y + x) mod 5>
#
# Quantum modular subtract:
#   |x>|y> -> |x>|(y - x) mod 5>
#
# Valid input values are always:
#   0 <= value < MODULUS
#
# For MODULUS = 5:
#   valid values:   0, 1, 2, 3, 4
#   invalid states: 5, 6, 7
# ---------------------------------------------------------------------

MODULUS = 5
X_VALUE = 2

N_QUBITS = math.ceil(math.log2(MODULUS))


# ---------------------------------------------------------------------
# Basic ripple-carry helper gates
# ---------------------------------------------------------------------

def maj(circuit, qa, qb, qc):
    """
    Majority operation.

    Gate sequence:
        cx c, b
        cx c, a
        ccx a, b, c
    """
    circuit.cx(qc, qb)
    circuit.cx(qc, qa)
    circuit.ccx(qa, qb, qc)


def uma_rc(circuit, qa, qb, qc):
    """
    Ripple-carry UMA operation.

    Gate sequence:
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


def controlled_x(circuit, controls, target):
    """
    Apply X to target controlled by zero or more controls.
    """
    controls = list(controls)

    if len(controls) == 0:
        circuit.x(target)
    elif len(controls) == 1:
        circuit.cx(controls[0], target)
    else:
        circuit.mcx(controls, target)


def controlled_cx(circuit, controls, control, target):
    """
    Controlled version of cx(control, target).
    """
    controlled_x(circuit, list(controls) + [control], target)


def controlled_ccx(circuit, controls, control_1, control_2, target):
    """
    Controlled version of ccx(control_1, control_2, target).
    """
    controlled_x(circuit, list(controls) + [control_1, control_2], target)


def controlled_maj(circuit, controls, qa, qb, qc):
    """
    Controlled MAJ operation.
    """
    controlled_cx(circuit, controls, qc, qb)
    controlled_cx(circuit, controls, qc, qa)
    controlled_ccx(circuit, controls, qa, qb, qc)


def controlled_uma_rc(circuit, controls, qa, qb, qc):
    """
    Controlled UMA operation.
    """
    controlled_x(circuit, controls, qb)
    controlled_cx(circuit, controls, qa, qb)
    controlled_ccx(circuit, controls, qa, qb, qc)
    controlled_x(circuit, controls, qb)
    controlled_cx(circuit, controls, qc, qa)
    controlled_cx(circuit, controls, qc, qb)


# ---------------------------------------------------------------------
# Generic ripple-carry addition helpers
# ---------------------------------------------------------------------

def encode_classical_value(circuit, value, qubits):
    """
    Encode a classical integer into a quantum register using X gates.

    Applying this function twice with the same value uncomputes the register.
    """
    register_size = len(qubits)
    value = value % (2 ** register_size)

    for i in range(register_size):
        if (value >> i) & 1:
            circuit.x(qubits[i])


def add_quantum_ripple_carry(circuit, x_qubits, y_qubits, carry_ancilla, overflow_bit=None):
    """
    Ripple-carry addition.

    Operation:
        |x>|y>|0> -> |x>|x + y mod 2^n>|0>

    If overflow_bit is provided, the overflow is copied into it.
    """
    n = len(y_qubits)

    maj(circuit, carry_ancilla, y_qubits[0], x_qubits[0])

    for i in range(n - 1):
        maj(circuit, x_qubits[i], y_qubits[i + 1], x_qubits[i + 1])

    if overflow_bit is not None:
        circuit.cx(x_qubits[n - 1], overflow_bit)

    for i in range(n - 1, 0, -1):
        uma_rc(circuit, x_qubits[i - 1], y_qubits[i], x_qubits[i])

    uma_rc(circuit, carry_ancilla, y_qubits[0], x_qubits[0])


def controlled_add_quantum_ripple_carry(
    circuit,
    controls,
    x_qubits,
    y_qubits,
    carry_ancilla,
    overflow_bit=None
):
    """
    Controlled ripple-carry addition.
    """
    controls = list(controls)
    n = len(y_qubits)

    controlled_maj(circuit, controls, carry_ancilla, y_qubits[0], x_qubits[0])

    for i in range(n - 1):
        controlled_maj(circuit, controls, x_qubits[i], y_qubits[i + 1], x_qubits[i + 1])

    if overflow_bit is not None:
        controlled_cx(circuit, controls, x_qubits[n - 1], overflow_bit)

    for i in range(n - 1, 0, -1):
        controlled_uma_rc(circuit, controls, x_qubits[i - 1], y_qubits[i], x_qubits[i])

    controlled_uma_rc(circuit, controls, carry_ancilla, y_qubits[0], x_qubits[0])


def add_classical_ripple_carry(circuit, value, y_qubits, helper_qubits):
    """
    Add a classical value into y modulo 2^n.

    helper_qubits layout:
        helper[0]      = carry ancilla
        helper[1:n+1]  = temporary encoded classical value
    """
    n = len(y_qubits)

    carry_ancilla = helper_qubits[0]
    x_qubits = helper_qubits[1:n + 1]

    encode_classical_value(circuit, value, x_qubits)

    add_quantum_ripple_carry(
        circuit=circuit,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        carry_ancilla=carry_ancilla
    )

    encode_classical_value(circuit, value, x_qubits)


def controlled_add_classical_ripple_carry(circuit, controls, value, y_qubits, helper_qubits):
    """
    Controlled classical addition into y modulo 2^n.
    """
    n = len(y_qubits)

    carry_ancilla = helper_qubits[0]
    x_qubits = helper_qubits[1:n + 1]

    encode_classical_value(circuit, value, x_qubits)

    controlled_add_quantum_ripple_carry(
        circuit=circuit,
        controls=controls,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        carry_ancilla=carry_ancilla
    )

    encode_classical_value(circuit, value, x_qubits)


# ---------------------------------------------------------------------
# Generic modular arithmetic helpers
# ---------------------------------------------------------------------

def add_classical_modulo_rc(
    circuit,
    value,
    y_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus
):
    """
    Add a classical value into y modulo modulus.

    Operation:
        |y>|0>|0>|0...0> -> |(y + value) mod modulus>|0>|0>|0...0>

    Register expectations:
        y_qubits        = n data qubits
        overflow_bit    = 1 overflow/work bit
        correction_flag = 1 flag/work bit
        helper_qubits   = n + 2 helper qubits

    This is parameterized by modulus and register size.
    """
    n = len(y_qubits)

    y_with_overflow = list(y_qubits) + [overflow_bit]

    # Step 1:
    # Compute y + value - modulus.
    add_classical_ripple_carry(
        circuit=circuit,
        value=value - modulus,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    # Step 2:
    # If the overflow bit is 1, then y + value was below modulus
    # after subtracting modulus, so we need to add modulus back.
    circuit.cx(overflow_bit, correction_flag)

    controlled_add_classical_ripple_carry(
        circuit=circuit,
        controls=[correction_flag],
        value=modulus,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    # Step 3:
    # Reset the correction flag.
    add_classical_ripple_carry(
        circuit=circuit,
        value=-value,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    circuit.cx(overflow_bit, correction_flag)
    circuit.x(correction_flag)

    add_classical_ripple_carry(
        circuit=circuit,
        value=value,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )


def subtract_classical_modulo_rc(
    circuit,
    value,
    y_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus
):
    """
    Subtract a classical value from y modulo modulus.

    Operation:
        |y> -> |(y - value) mod modulus>
    """
    add_classical_modulo_rc(
        circuit=circuit,
        value=-value,
        y_qubits=y_qubits,
        overflow_bit=overflow_bit,
        correction_flag=correction_flag,
        helper_qubits=helper_qubits,
        modulus=modulus
    )


def controlled_add_classical_modulo_rc(
    circuit,
    controls,
    value,
    y_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus
):
    """
    Controlled classical modular addition.

    If controls are active:
        |y> -> |(y + value) mod modulus>
    """
    controls = list(controls)
    y_with_overflow = list(y_qubits) + [overflow_bit]

    # Step 1:
    # Controlled add value.
    controlled_add_classical_ripple_carry(
        circuit=circuit,
        controls=controls,
        value=value,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    # Step 2:
    # Subtract modulus unconditionally.
    add_classical_ripple_carry(
        circuit=circuit,
        value=-modulus,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    # Step 3:
    # Use overflow to decide whether modulus must be restored.
    circuit.cx(overflow_bit, correction_flag)

    controlled_add_classical_ripple_carry(
        circuit=circuit,
        controls=[correction_flag],
        value=modulus,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    # Step 4:
    # Reset the correction flag.
    add_classical_ripple_carry(
        circuit=circuit,
        value=-value,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )

    controlled_x(
        circuit=circuit,
        controls=controls + [overflow_bit],
        target=correction_flag
    )

    circuit.x(correction_flag)

    add_classical_ripple_carry(
        circuit=circuit,
        value=value,
        y_qubits=y_with_overflow,
        helper_qubits=helper_qubits
    )


def add_quantum_modulo_rc(
    circuit,
    x_qubits,
    y_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus,
    multiplier=1
):
    """
    Add multiplier * x into y modulo modulus.

    Operation:
        |x>|y>|0...0> -> |x>|(y + multiplier*x) mod modulus>|0...0>

    This is built using controlled classical modular additions.
    """
    for i, control_qubit in enumerate(x_qubits):
        controlled_value = (multiplier * (2 ** i)) % modulus

        controlled_add_classical_modulo_rc(
            circuit=circuit,
            controls=[control_qubit],
            value=controlled_value,
            y_qubits=y_qubits,
            overflow_bit=overflow_bit,
            correction_flag=correction_flag,
            helper_qubits=helper_qubits,
            modulus=modulus
        )


def subtract_quantum_modulo_rc(
    circuit,
    x_qubits,
    y_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus
):
    """
    Subtract x from y modulo modulus.

    Operation:
        |x>|y> -> |x>|(y - x) mod modulus>
    """
    add_quantum_modulo_rc(
        circuit=circuit,
        x_qubits=x_qubits,
        y_qubits=y_qubits,
        overflow_bit=overflow_bit,
        correction_flag=correction_flag,
        helper_qubits=helper_qubits,
        modulus=modulus,
        multiplier=-1
    )


# ---------------------------------------------------------------------
# Circuit 1:
# rc_adder_add_classical_modular
#
# Operation:
#   |y> -> |(y + X_VALUE) mod MODULUS>
#
# Qubit layout for MODULUS = 5:
#   0, 1, 2       = y
#   3             = overflow
#   4             = correction flag
#   5, 6, 7, 8, 9 = helper
#
# Total qubits:
#   2n + 4
# ---------------------------------------------------------------------

y_add_classical_modular = QuantumRegister(N_QUBITS, "y_add_cmod")
overflow_add_classical_modular = QuantumRegister(1, "overflow_add_cmod")
flag_add_classical_modular = QuantumRegister(1, "flag_add_cmod")
helper_add_classical_modular = QuantumRegister(N_QUBITS + 2, "helper_add_cmod")

rc_adder_add_classical_modular_circuit = QuantumCircuit(
    y_add_classical_modular,
    overflow_add_classical_modular,
    flag_add_classical_modular,
    helper_add_classical_modular,
    name="rc_adder_add_classical_modular"
)

add_classical_modulo_rc(
    circuit=rc_adder_add_classical_modular_circuit,
    value=X_VALUE,
    y_qubits=list(y_add_classical_modular),
    overflow_bit=overflow_add_classical_modular[0],
    correction_flag=flag_add_classical_modular[0],
    helper_qubits=list(helper_add_classical_modular),
    modulus=MODULUS
)


# ---------------------------------------------------------------------
# Circuit 2:
# rc_adder_subtract_classical_modular
#
# Operation:
#   |y> -> |(y - X_VALUE) mod MODULUS>
#
# Qubit layout is the same as classical modular add.
# Total qubits:
#   2n + 4
# ---------------------------------------------------------------------

y_subtract_classical_modular = QuantumRegister(N_QUBITS, "y_sub_cmod")
overflow_subtract_classical_modular = QuantumRegister(1, "overflow_sub_cmod")
flag_subtract_classical_modular = QuantumRegister(1, "flag_sub_cmod")
helper_subtract_classical_modular = QuantumRegister(N_QUBITS + 2, "helper_sub_cmod")

rc_adder_subtract_classical_modular_circuit = QuantumCircuit(
    y_subtract_classical_modular,
    overflow_subtract_classical_modular,
    flag_subtract_classical_modular,
    helper_subtract_classical_modular,
    name="rc_adder_subtract_classical_modular"
)

subtract_classical_modulo_rc(
    circuit=rc_adder_subtract_classical_modular_circuit,
    value=X_VALUE,
    y_qubits=list(y_subtract_classical_modular),
    overflow_bit=overflow_subtract_classical_modular[0],
    correction_flag=flag_subtract_classical_modular[0],
    helper_qubits=list(helper_subtract_classical_modular),
    modulus=MODULUS
)


# ---------------------------------------------------------------------
# Circuit 3:
# rc_adder_add_quantum_modular
#
# Operation:
#   |x>|y> -> |x>|(y + x) mod MODULUS>
#
# Qubit layout for MODULUS = 5:
#   0, 1, 2             = x
#   3, 4, 5             = y
#   6                   = overflow
#   7                   = correction flag
#   8, 9, 10, 11, 12    = helper
#
# Total qubits:
#   3n + 4
# ---------------------------------------------------------------------

x_add_quantum_modular = QuantumRegister(N_QUBITS, "x_add_qmod")
y_add_quantum_modular = QuantumRegister(N_QUBITS, "y_add_qmod")
overflow_add_quantum_modular = QuantumRegister(1, "overflow_add_qmod")
flag_add_quantum_modular = QuantumRegister(1, "flag_add_qmod")
helper_add_quantum_modular = QuantumRegister(N_QUBITS + 2, "helper_add_qmod")

rc_adder_add_quantum_modular_circuit = QuantumCircuit(
    x_add_quantum_modular,
    y_add_quantum_modular,
    overflow_add_quantum_modular,
    flag_add_quantum_modular,
    helper_add_quantum_modular,
    name="rc_adder_add_quantum_modular"
)

add_quantum_modulo_rc(
    circuit=rc_adder_add_quantum_modular_circuit,
    x_qubits=list(x_add_quantum_modular),
    y_qubits=list(y_add_quantum_modular),
    overflow_bit=overflow_add_quantum_modular[0],
    correction_flag=flag_add_quantum_modular[0],
    helper_qubits=list(helper_add_quantum_modular),
    modulus=MODULUS,
    multiplier=1
)


# ---------------------------------------------------------------------
# Circuit 4:
# rc_adder_subtract_quantum_modular
#
# Operation:
#   |x>|y> -> |x>|(y - x) mod MODULUS>
#
# Qubit layout is the same as quantum modular add.
# Total qubits:
#   3n + 4
# ---------------------------------------------------------------------

x_subtract_quantum_modular = QuantumRegister(N_QUBITS, "x_sub_qmod")
y_subtract_quantum_modular = QuantumRegister(N_QUBITS, "y_sub_qmod")
overflow_subtract_quantum_modular = QuantumRegister(1, "overflow_sub_qmod")
flag_subtract_quantum_modular = QuantumRegister(1, "flag_sub_qmod")
helper_subtract_quantum_modular = QuantumRegister(N_QUBITS + 2, "helper_sub_qmod")

rc_adder_subtract_quantum_modular_circuit = QuantumCircuit(
    x_subtract_quantum_modular,
    y_subtract_quantum_modular,
    overflow_subtract_quantum_modular,
    flag_subtract_quantum_modular,
    helper_subtract_quantum_modular,
    name="rc_adder_subtract_quantum_modular"
)

subtract_quantum_modulo_rc(
    circuit=rc_adder_subtract_quantum_modular_circuit,
    x_qubits=list(x_subtract_quantum_modular),
    y_qubits=list(y_subtract_quantum_modular),
    overflow_bit=overflow_subtract_quantum_modular[0],
    correction_flag=flag_subtract_quantum_modular[0],
    helper_qubits=list(helper_subtract_quantum_modular),
    modulus=MODULUS
)