"""Template for creating new gate tests under `gate_tests/`.

Copy this file to `../gate_tests/test_MyGate.py` and edit `build_circuit()` and
`validate_result()`.
"""

from hypothesis import HealthCheck, given, settings, strategies as st
from qiskit import QuantumCircuit, QuantumRegister

from test_framework import (
    compile_to_parse_tree,
    print_register_state,
    run_simulation,
    setup_project_paths,
)

setup_project_paths()

NUMBER_OF_INPUT_QUBITS = 1
REGISTER_NAME = "test"


def build_circuit() -> QuantumCircuit:
    """Build your Qiskit circuit under test."""
    qc = QuantumCircuit(QuantumRegister(NUMBER_OF_INPUT_QUBITS + 1, REGISTER_NAME))
    qc.x(0)
    return qc


def validate_result(state_bits, sim_state) -> None:
    """Add assertions for your property/check here."""
    assert REGISTER_NAME in sim_state
    assert len(sim_state[REGISTER_NAME]) == NUMBER_OF_INPUT_QUBITS + 1


PARSE_TREE = compile_to_parse_tree(
    build_circuit(),
    circuit_name="Template Test Circuit",
    optimise_circuit=False,
    show_decomposed_circuit=True,
    gate_set_to_use=["x", "cx", "ccx", "rz", "h"],
)


@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(
        st.booleans(),
        min_size=NUMBER_OF_INPUT_QUBITS,
        max_size=NUMBER_OF_INPUT_QUBITS,
    ),
)
def run_property_test(state_bits):
    """Entry point for Hypothesis-based simulation checks."""
    sim_state = run_simulation(
        PARSE_TREE,
        state_bits,
        register_name=REGISTER_NAME,
        include_output_qubit=True,
    )
    print("generated state", state_bits)
    print_register_state(sim_state, register_name=REGISTER_NAME)
    validate_result(state_bits, sim_state)


if __name__ == "__main__":
    run_property_test()
