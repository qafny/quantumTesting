from qiskit import QuantumCircuit, transpile, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import IntegerComparator
from qiskit_aer import AerSimulator
import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from AST_Scripts.simulator import CoqNVal,CoqYVal, Simulator
N_COUNT = 8

qr1 = QuantumRegister(N_COUNT, 'q1')
qr2 = QuantumRegister(N_COUNT, 'q2')
cl1 = ClassicalRegister(1, 'c1')

qc = QuantumCircuit(qr1, qr2, cl1)
comparer = IntegerComparator(num_state_qubits=(N_COUNT), value=111, geq=False)
for q in range(N_COUNT):
    qc.h(qr1[q])
qc.append(comparer, range(comparer.num_qubits))
qc.measure(qr2[0], cl1[0])

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(qc, circuitName="Example Circuit 1", optimiseCircuit=False, showDecomposedCircuit=True)
    return new_tree

parseTree = get_tree()

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=N_COUNT, max_size=N_COUNT),
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

simulate_circuit(N_COUNT, parseTree)

