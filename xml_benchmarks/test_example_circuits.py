from antlr4 import InputStream, CommonTokenStream
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)

from AST_Scripts.XMLExpLexer import XMLExpLexer
from AST_Scripts.XMLExpParser import XMLExpParser
from AST_Scripts.ProgramTransformer import ProgramTransformer
from AST_Scripts.ValidatorProgramVisitors import SimulatorValidator
from AST_Scripts.Retrievers import MatchCounterRetriever
from AST_Scripts.simulator import CoqNVal, Simulator, bit_array_to_int, to_binary_arr
import math
import qiskit
sys.path.append(parent_dir+'/qiskit-to-xmlprogrammer')
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from qiskit import transpile
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGInNode, DAGOpNode, DAGNode, DAGOutNode
from qiskit.visualization import dag_drawer
import graphviz
import os
import sys
from qiskit.circuit.library.arithmetic import FullAdderGate

from AST_Scripts.XMLProgrammer import QXProgram, QXQID, QXCU, QXX, QXH, QXRZ, QXRY, QXRoot

# Ensure graphviz is in the PATH (for dag drawing)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

# --------------------------- EXAMPLE CIRCUITS ---------------------------------

# ----- 1: Common gates

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.h(1)
qc.x(1)
qc.measure([0,1], [0,1])
qcEx1 = qc.copy()

# dag_img = dag_drawer(dagEx1, style="color")
# dag_img.save('dagEx1.png')

# ----- 2: All qiskit gates

qc = QuantumCircuit(3, 1)
qc.h(0)
qc.cx(0, 1)
qc.x(2)
qc.z(2)
qc.s(1)
qc.t(0)
qc.cz(1, 2)
qc.sdg(1)
qc.tdg(0)
qc.y(0)
qcEx2 = qc.copy()

# ----- 3: 3-Qubit GHZ

qc = QuantumCircuit(3, 0)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qcEx3 = qc.copy()

# -------------------------- COMPILE TO XMLPROGRAMMER --------------------------

visitor = QCtoXMLProgrammer()

# visitor.startVisit(qcEx1, circuitName="Example Circuit 1", optimiseCircuit=True, showDecomposedCircuit=True)
# visitor.startVisit(qcEx2, circuitName="Example Circuit 2", optimiseCircuit=True)
# visitor.startVisit(qcEx3, circuitName="Example Circuit 3", optimiseCircuit=True)

# NOTE:: test how to run the code.

def read_program(file_path: str):
    # with open(file_path, 'r') as f:
    #     str = f.read()
    # i_stream = InputStream(str)
    # lexer = XMLExpLexer(i_stream)
    # t_stream = CommonTokenStream(lexer)
    # parser = XMLExpParser(t_stream)
    # tree = parser.root()
    transform = QCtoXMLProgrammer()
    output = visitor.startVisit(qcEx1, circuitName="Example Circuit 1", optimiseCircuit=True, showDecomposedCircuit=False)
    # type needs to be QXRoot
    new_tree = transform.visitProgram(output)

    return new_tree


def get_tree():
    #new_tree = read_program(f"{os.path.dirname(os.path.realpath(__file__))}/mutants/mutant_38.xml")
    new_tree = visitor.startVisit(qcEx3, circuitName="Example Circuit 1", optimiseCircuit=True, showDecomposedCircuit=True)
    print ('new tree type', type(new_tree))
    valid_tree = True

    # try:
    #     # Validation of the Constraints.
    #     # Added per Dr. Li's suggestion on 11/16 to scoop out the validator behaviour out of the simulator as there can be
    #     # programs which does not always need to follow constraints like only having 1 app tag.
    #     validator = SimulatorValidator()
    #     validator.visitProgram((new_tree))

    #     # Non-Decreasing Recursive Fixed Point Factor Check
    # except Exception as e:
    #     print('\n ==============', e, '==============')
    #     valid_tree = False

    # retriever = MatchCounterRetriever()
    # retriever.visitProgram(new_tree)
    return new_tree, valid_tree

parsetree = get_tree()[0]

from hypothesis import given, strategies as st, assume, settings, HealthCheck

def simulate_circuit(x_array_value, y_array_value, c_array_value, num_qubits, parse_tree):
    val_array_x = to_binary_arr(x_array_value, num_qubits)
    val_array_y = to_binary_arr(y_array_value, num_qubits)
    num_qubits_ca = 1
    val_array_ca = to_binary_arr(c_array_value, num_qubits_ca)

    state = dict(
        {"test": [CoqNVal([True] * 5, 0)]
         })
    environment = dict(
        {"xa": num_qubits,
         "ya": num_qubits,
         "ca": num_qubits_ca,
         })

    simulator = Simulator(state, environment)
    print('parse tree type', type(parse_tree))
    simulator.visitProgram(parse_tree)
    new_state = simulator.state
    return new_state

def process_bitwise_test_cases(test_cases: list):
    # pt_output = read_program(f"{os.path.dirname(os.path.realpath(__file__))}/cl_adder_good.xml")
    # print('pt_output', pt_output)
    # print('pt_output type', type(pt_output))
    insts = []
    for test_case in test_cases:
        na = test_case['na']
        ca = test_case['ca']
        xa = test_case['xa']
        ya = test_case['ya']

        expected = (xa + ya) % (2 ** na)
        new_state = simulate_circuit(xa, ya, ca, na, parsetree)
        # calculated = bit_array_to_int(new_state.get('ya')[0].getBits(), na)

        # insts.append((na, expected, calculated))

    return new_state

test_cases_for_bitwise = [
    {"na": 20, "xa": 5, "ya": 5, "ca": 0, "expected": 10}
]

bitwise_test_instances = process_bitwise_test_cases(test_cases_for_bitwise)