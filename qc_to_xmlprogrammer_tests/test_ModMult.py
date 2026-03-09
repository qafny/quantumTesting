from qiskit import QuantumCircuit
import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from AST_Scripts.simulator import CoqNVal,CoqYVal, Simulator

number_of_input_qubits = 4

U = QuantumCircuit(number_of_input_qubits)

U.swap(2, 3)
U.swap(1, 2)
U.swap(0, 1)

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(U, circuitName="Example Circuit 1", optimiseCircuit=False, showDecomposedCircuit=True)
    return new_tree

parseTree = get_tree()

parseTree = get_tree()

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=number_of_input_qubits, max_size=number_of_input_qubits),
)
def simulate_circuit(num_qubits, parse_tree, state_bits):
    val = []
    for i in range(num_qubits):
        val += [CoqNVal(state_bits[i],phase=0)]
    val += [CoqNVal(False, phase=0)]
    state = {"test": val}
    #state = {"test": [CoqNVal(state_bits+[False], phase=0)]}
    environment = {"test": num_qubits + 1}
    sim = Simulator(state, environment)
    sim.visitProgram(parseTree)
    # TODO: validate properties for each instance
    post_sim_state = sim.state
    vals = post_sim_state['test']
    for val in vals:
        if isinstance(val, CoqNVal):
            print('bit', val.getBit())
        elif isinstance(val, CoqYVal):
            print('zero: ', val.getZero())
            print('one: ', val.getOne())
    #print(post_sim_state['test'])

simulate_circuit(number_of_input_qubits, parseTree)