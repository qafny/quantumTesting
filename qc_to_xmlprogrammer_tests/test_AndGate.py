from qiskit.circuit.library import AndGate
import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from AST_Scripts.simulator import CoqNVal, Simulator
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck

os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

testGate = AndGate(num_variable_qubits=3)
qc = QuantumCircuit(QuantumRegister(4))
qc.append(testGate, [0,1,2,3])

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(qc, circuitName="Example Circuit 1", optimiseCircuit=False, showDecomposedCircuit=True)
    return new_tree

parseTree = get_tree()

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=3, max_size=3),
)
def simulate_circuit(num_qubits, parse_tree, state_bits):
    print('generated state', state_bits)
    state = {"test": [CoqNVal(state_bits+[False], phase=0)]}
    environment = {"xa": num_qubits}
    sim = Simulator(state, environment)
    sim.visitProgram(parseTree)
    # TODO: validate properties for each instance
    post_sim_state = sim.state
    print(post_sim_state['test'][0].getBits())

simulate_circuit(3, parseTree)

