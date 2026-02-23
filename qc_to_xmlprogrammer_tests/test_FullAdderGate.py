from qiskit.circuit.library import FullAdderGate
import os, sys

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')

from AST_Scripts.simulator import CoqNVal, CoqYVal, Simulator
from qiskit import QuantumCircuit, QuantumRegister
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck


testGate = FullAdderGate(num_state_qubits=2)
number_of_input_qubits = testGate.num_qubits

qc = QuantumCircuit(QuantumRegister(number_of_input_qubits))
qc.append(testGate, list(range(number_of_input_qubits)))

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(
        qc,
        circuitName="FullAdder Circuit",
        optimiseCircuit=False,
        showDecomposedCircuit=True
    )
    return new_tree

parseTree = get_tree()


def le_bits_to_int(bits):
    val = 0
    for i, b in enumerate(bits):
        if b:
            val |= (1 << i)
    return val


def int_to_le_bits(x, nbits):
    return [(x >> i) & 1 == 1 for i in range(nbits)]


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
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

    # # manual test.
    # cin = int(state_bits[0])
    # a_bits = state_bits[1:3]
    # b_bits = state_bits[3:5]
    # cout_in = int(state_bits[5])
    # a = le_bits_to_int(a_bits)
    # b = le_bits_to_int(b_bits)
    # s = cin + a + b
    # sum_bits = int_to_le_bits(s, 3)
    # expected = state_bits.copy()
    # expected[0] = sum_bits[0]
    # expected[3] = sum_bits[1]
    # expected[4] = sum_bits[2]
    # assert output_bits == expected


simulate_circuit()