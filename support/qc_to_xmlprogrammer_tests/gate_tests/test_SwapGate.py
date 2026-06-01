from qiskit.circuit.library import SwapGate
import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
sys.path.insert(0, os.path.join(parent_dir, "qc_to_xmlprogrammer_tests", "framework"))

from hypothesis import HealthCheck, given, settings, strategies as st
from qiskit import QuantumCircuit, QuantumRegister

from test_framework import (
    compile_to_parse_tree,
    print_register_state,
    run_simulation,
    setup_project_paths,
)

setup_project_paths()

os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

number_of_input_qubits = 2
testGate = SwapGate()
qc = QuantumCircuit(QuantumRegister(2))
qc.append(testGate, [0, 1])

parseTree = compile_to_parse_tree(
    qc,
    circuit_name="Example Circuit 1",
    optimise_circuit=False,
    show_decomposed_circuit=True,
    gate_set_to_use=["x", "cx", "ccx", "rz", "h"],
)

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=number_of_input_qubits, max_size=number_of_input_qubits),
)
def test_SwapGate(state_bits):
    print('generated state', state_bits)
    post_sim_state = run_simulation(
        parseTree,
        state_bits,
        register_name="test",
        include_output_qubit=False,
    )
    vals = post_sim_state["test"]
    assert vals[0].getBit() == state_bits[1]
    assert vals[1].getBit() == state_bits[0]
    print_register_state(post_sim_state, register_name="test")

test_SwapGate()

