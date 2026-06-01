from qiskit import QuantumCircuit, transpile, QuantumRegister, ClassicalRegister
from qiskit.visualization import plot_histogram
from qiskit.circuit.library import HalfAdderGate
from qiskit_aer import AerSimulator
import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from AST_Scripts.simulator import CoqNVal,CoqYVal, Simulator
from hypothesis import given, strategies as st, assume, settings, HealthCheck

N_COUNT = 8
qr1 = QuantumRegister(N_COUNT, 'q1') # 0-7,
qr2 = QuantumRegister(N_COUNT, 'q2') # 8-15,
qr3 = QuantumRegister(N_COUNT, 'q3') # 16-23
qr4 = QuantumRegister(N_COUNT, 'q4') # 24-31
qr5 = QuantumRegister(N_COUNT, 'q5') # 32-39
cl1 = ClassicalRegister(N_COUNT, 'c1')
cl2 = ClassicalRegister(N_COUNT, 'c2')
qr6 = QuantumRegister(N_COUNT+1, 'q6')
cl3 = ClassicalRegister(1, 'c3')
qc = QuantumCircuit(qr1, qr2, qr3, qr4, qr5, qr6, cl1, cl2, cl3)

for q in range(8,16):
    qc.h(q)
adder = HalfAdderGate(num_state_qubits=8)
oneAdder = HalfAdderGate(num_state_qubits=4)
qc.x(range(8,16))
qc.append(adder, [*range(0,16), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(8,16))
qc.x(range(16,24))
qc.append(adder, [*range(0,8),*range(16,24), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(16,24))
qc.x(range(24,32))
qc.append(adder, [*range(0,8),*range(24,32), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(24,32))
qc.x(range(32, 40))
qc.append(adder, [*range(0,8),*range(32, 40), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(32, 40))
qc.x(range(16,24))
qc.append(adder, [*range(8,16),*range(16,24), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(16,24))
qc.x(range(24,32))
qc.append(adder, [*range(8,16),*range(24,32), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(24,32))
qc.x(range(32,40))
qc.append(adder, [*range(8,16),*range(32,40), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(32,40))
qc.x(range(24,32))
qc.append(adder, [*range(16,24),*range(24,32), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(24,32))
qc.x(range(32,40))
qc.append(adder, [*range(16,24),*range(32,40), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(32,40))
qc.x(range(32,40))
qc.append(adder, [*range(24,32),*range(32,40), qr6[0]])
qc.append(oneAdder, qr6)
qc.x(range(32,40))

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