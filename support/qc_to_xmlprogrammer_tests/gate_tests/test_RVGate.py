from qiskit.circuit.library import RVGate
from qiskit import QuantumCircuit, QuantumRegister
import sys
import os
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0,parent_dir)
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from AST_Scripts.simulator import CoqNVal,CoqYVal, Simulator
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import math


number_of_input_qubits = 1
visitor = QCtoXMLProgrammer()

def get_tree(qc: QuantumCircuit):
    return visitor.startVisit(qc, circuitName="Qiskit Circuit RV gate", optimiseCircuit=False, showDecomposedCircuit=True)


@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    state_bits=st.lists(st.booleans(), min_size=number_of_input_qubits, max_size=number_of_input_qubits),
    vx=st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False, allow_infinity=False),
    vy=st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False, allow_infinity=False),
    vz=st.floats(min_value=-math.pi, max_value=math.pi, allow_nan=False, allow_infinity=False),
)
def simulate_circuit(num_qubits, state_bits, vx, vy, vz):
    print("generated state", state_bits)
    print("vector:", vx, vy, vz)
    testGate = RVGate(vx, vy, vz)
    qc = QuantumCircuit(QuantumRegister(number_of_input_qubits))
    qc.append(testGate, [0])   
    val = []
    for i in range(num_qubits):
        val += [CoqNVal(state_bits[i],phase=0)]
    state = {"test": val}
    environment = {"test": num_qubits}
    sim = Simulator(state, environment)
    sim.visitProgram(get_tree(qc))
    post_sim_state = sim.state
    vals = post_sim_state['test']
    for val in vals:
        if isinstance(val, CoqNVal):
            print(val.getBit())
        elif isinstance(val, CoqYVal):
            print(val.getZero())
            print(val.getOne())

simulate_circuit(number_of_input_qubits)