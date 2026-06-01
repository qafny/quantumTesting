import os
import sys

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + "/qiskit-to-xmlprogrammer")
sys.path.insert(0, os.path.join(parent_dir, "qc_to_xmlprogrammer_tests", "framework"))

from hypothesis import given, strategies as st
from qiskit import QuantumCircuit

from AST_Scripts.XMLProgrammer import QXH, QXNum

from test_framework import (
    compile_to_parse_tree,
    print_register_state,
    run_simulation,
    setup_project_paths,
)

# Ensure graphviz is in the PATH (for dag drawing)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

# Keep project path setup consistent.
setup_project_paths()

# ----- 3: 3-Qubit GHZ

qc = QuantumCircuit(3, 3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure([0,1,2], [0,1,2])
qcEx3 = qc.copy()

# -------------------------- COMPILE TO XMLPROGRAMMER --------------------------
qcEx3_nom = qcEx3.remove_final_measurements(inplace=False)
parsetree = compile_to_parse_tree(
    qcEx3_nom,
    circuit_name="Example Circuit 1",
    optimise_circuit=True,
    show_decomposed_circuit=True,
    gate_set_to_use=["x", "cx", "ccx", "rz", "h"],
)

@given(first_qubit = st.sampled_from([True, False]))
def test_bitwise_test_cases(first_qubit):
    indicesOfQHX = [ind for ind, item in enumerate(parsetree._exps) if type(item) == QXH]
    for index in indicesOfQHX:
        parsetree._exps[index] = QXNum(0)

    state_bits = [first_qubit, False, False]
    new_state = run_simulation(
        parsetree,
        state_bits,
        register_name="test",
        include_output_qubit=False,
    )
    vals = new_state["test"]
    assert vals[0].getBit() == vals[1].getBit() == vals[2].getBit()
    print_register_state(new_state, register_name="test")
    # if (new_state['test'][0].getBits()[0] == new_state['test'][0].getBits()[1] == new_state['test'][0].getBits()[2]):
    #     assert True
    # else:
    #     assert False
test_bitwise_test_cases()