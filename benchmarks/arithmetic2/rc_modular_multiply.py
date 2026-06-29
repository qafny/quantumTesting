import math

from qiskit import QuantumCircuit, QuantumRegister
from benchmarks.arithmetic2.rc_modular_circuits import add_quantum_modulo_rc, controlled_add_classical_modulo_rc

MODULUS = 5
N_QUBITS = math.ceil(math.log2(MODULUS))

# ---------------------------------------------------------------------
# This computes:
#
#   result = (MULTIPLIER * x) mod MODULUS
#
# For now:
#   MODULUS = 5
#   MULTIPLIER = 2
#
# Valid x inputs:
#   0, 1, 2, 3, 4
#
# Expected mapping:
#   0 -> 0
#   1 -> 2
#   2 -> 4
#   3 -> 1
#   4 -> 3
# ---------------------------------------------------------------------

MULTIPLIER = 2

if math.gcd(MULTIPLIER, MODULUS) != 1:
    raise ValueError(
        f"MULTIPLIER must be coprime with MODULUS. "
        f"Got MULTIPLIER={MULTIPLIER}, MODULUS={MODULUS}."
    )

# ---------------------------------------------------------------------
# Helper: controlled modular multiplication
#
# This builds:
#
#   if control == 1:
#       result += MULTIPLIER * x mod MODULUS
#
# It is implemented as repeated controlled modular additions.
# For each input bit x[i], conditionally add:
#
#   MULTIPLIER * 2^i mod MODULUS
#
# into the result register.
# ---------------------------------------------------------------------

def controlled_modular_multiplication_rc(
    circuit,
    control_qubit,
    x_qubits,
    result_qubits,
    overflow_bit,
    correction_flag,
    helper_qubits,
    modulus,
    multiplier
):
    """
    Controlled modular multiplication.

    Operation:
        if control == 1:
            |x>|result> -> |x>|result + multiplier*x mod modulus>

    Result starts as 0, so the final result becomes:
        |result> = |multiplier*x mod modulus>
    """
    for i, x_bit in enumerate(x_qubits):
        controlled_value = (multiplier * (2 ** i)) % modulus

        if controlled_value == 0:
            continue

        controlled_add_classical_modulo_rc(
            circuit=circuit,
            controls=[control_qubit, x_bit],
            value=controlled_value,
            y_qubits=result_qubits,
            overflow_bit=overflow_bit,
            correction_flag=correction_flag,
            helper_qubits=helper_qubits,
            modulus=modulus
        )

# ---------------------------------------------------------------------
# rc_modular_multiplication
#
# Operation:
#   |x>|result=0>|helper=0> -> |x>|MULTIPLIER*x mod MODULUS>|helper=0>
#
# Qubit layout for MODULUS = 5, N_QUBITS = 3:
#
#   0, 1, 2          = x input register
#   3, 4, 5          = result register
#   6                = overflow bit
#   7                = correction flag
#   8, 9, 10, 11, 12 = helper register
#
# Total qubits:
#   3n + 4
# ---------------------------------------------------------------------

x_modmul = QuantumRegister(N_QUBITS, "x_modmul")
result_modmul = QuantumRegister(N_QUBITS, "result_modmul")
overflow_modmul = QuantumRegister(1, "overflow_modmul")
flag_modmul = QuantumRegister(1, "flag_modmul")
helper_modmul = QuantumRegister(N_QUBITS + 2, "helper_modmul")

rc_modular_multiplication_circuit = QuantumCircuit(
    x_modmul,
    result_modmul,
    overflow_modmul,
    flag_modmul,
    helper_modmul,
    name="rc_modular_multiplication"
)

add_quantum_modulo_rc(
    circuit=rc_modular_multiplication_circuit,
    x_qubits=list(x_modmul),
    y_qubits=list(result_modmul),
    overflow_bit=overflow_modmul[0],
    correction_flag=flag_modmul[0],
    helper_qubits=list(helper_modmul),
    modulus=MODULUS,
    multiplier=MULTIPLIER
)


# ---------------------------------------------------------------------
# rc_controlled_modular_multiplication
#
# Operation:
#   if control == 1:
#       |x>|result=0> -> |x>|MULTIPLIER*x mod MODULUS>
#   else:
#       |x>|result=0> -> |x>|0>
#
# Qubit layout for MODULUS = 5, N_QUBITS = 3:
#
#   0                = control qubit
#   1, 2, 3          = x input register
#   4, 5, 6          = result register
#   7                = overflow bit
#   8                = correction flag
#   9, 10, 11, 12, 13 = helper register
#
# Total qubits:
#   1 + 3n + 4
# ---------------------------------------------------------------------

control_cmodmul = QuantumRegister(1, "control_cmodmul")
x_cmodmul = QuantumRegister(N_QUBITS, "x_cmodmul")
result_cmodmul = QuantumRegister(N_QUBITS, "result_cmodmul")
overflow_cmodmul = QuantumRegister(1, "overflow_cmodmul")
flag_cmodmul = QuantumRegister(1, "flag_cmodmul")
helper_cmodmul = QuantumRegister(N_QUBITS + 2, "helper_cmodmul")

rc_controlled_modular_multiplication_circuit = QuantumCircuit(
    control_cmodmul,
    x_cmodmul,
    result_cmodmul,
    overflow_cmodmul,
    flag_cmodmul,
    helper_cmodmul,
    name="rc_controlled_modular_multiplication"
)

controlled_modular_multiplication_rc(
    circuit=rc_controlled_modular_multiplication_circuit,
    control_qubit=control_cmodmul[0],
    x_qubits=list(x_cmodmul),
    result_qubits=list(result_cmodmul),
    overflow_bit=overflow_cmodmul[0],
    correction_flag=flag_cmodmul[0],
    helper_qubits=list(helper_cmodmul),
    modulus=MODULUS,
    multiplier=MULTIPLIER
)