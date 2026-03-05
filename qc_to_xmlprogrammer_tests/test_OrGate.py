from qiskit.circuit.library import OrGate
from qiskit import QuantumCircuit, QuantumRegister
from AST_Scripts.simulator import CoqNVal,CoqYVal, Simulator
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck

number_of_input_qubits = 3
testGate = OrGate(num_variable_qubits=number_of_input_qubits)
qc = QuantumCircuit(QuantumRegister(4))
qc.append(testGate, [0,1,2,3])

visitor = QCtoXMLProgrammer()

def get_tree():
    new_tree = visitor.startVisit(qc, circuitName="Qiskit Circuit OR gate", optimiseCircuit=False, showDecomposedCircuit=True)
    return new_tree

parseTree = get_tree()

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=number_of_input_qubits, max_size=number_of_input_qubits),
)
def simulate_circuit(num_qubits, parse_tree, state_bits):
    print('generated state', state_bits)
    val = []
    for i in range(num_qubits):
        val += [CoqNVal(state_bits[i],phase=0)]
    val += [CoqNVal(False, phase=0)]
    state = {"test": val}
    environment = {"test": num_qubits}
    sim = Simulator(state, environment)
    sim.visitProgram(parseTree)
    post_sim_state = sim.state
    vals = post_sim_state['test']
    for val in vals:
        if isinstance(val, CoqNVal):
            print(val.getBit())
        elif isinstance(val, CoqYVal):
            print(val.getZero())
            print(val.getOne())

simulate_circuit(number_of_input_qubits, parseTree)
