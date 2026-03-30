from qiskit.circuit.library import XOR
import os, sys

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')

from AST_Scripts.simulator import CoqNVal, CoqYVal, Simulator
from qiskit import QuantumCircuit, QuantumRegister
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck


number_of_input_qubits = 10
amount =  0b1010101101
testGate = XOR(number_of_input_qubits, amount=amount)

qc = QuantumCircuit(QuantumRegister(number_of_input_qubits))
qc.append(testGate, list(range(number_of_input_qubits)))

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(
        qc,
        circuitName="XOR Circuit",
        optimiseCircuit=False,
        showDecomposedCircuit=True
    )
    return new_tree

parseTree = get_tree()


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=number_of_input_qubits, max_size=number_of_input_qubits),
)
def simulate_circuit(state_bits):

    val = []
    for i in range(number_of_input_qubits):
        val += [CoqNVal(state_bits[i], phase=0)]

    state = {"test": val}
    environment = {"test": number_of_input_qubits}

    sim = Simulator(state, environment)
    sim.visitProgram(parseTree)

    post_sim_state = sim.state
    vals = post_sim_state['test']

    output_bits = []
    for v in vals:
        if isinstance(v, CoqNVal):
            output_bits.append(v.getBit())
        elif isinstance(v, CoqYVal):
            pass

    # Oracle
    expected = state_bits.copy()
    for i in range(number_of_input_qubits):
        if (amount >> i) & 1:
            expected[i] = not expected[i]

    assert output_bits == expected


simulate_circuit()