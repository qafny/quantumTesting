from antlr4 import InputStream, CommonTokenStream
import sys
import os

# current_dir = os.path.dirname(os.path.realpath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.insert(0,parent_dir)
# sys.path.append('/Users/anshugsharma/VSCodeRepos/quantumTesting/qiskit-to-xmlprogrammer')
sys.path.append('/Users/anshugsharma/VSCodeRepos/quantumTesting')
print(sys.path)
from AST_Scripts.XMLExpLexer import XMLExpLexer
from AST_Scripts.XMLExpParser import XMLExpParser
from AST_Scripts.ProgramTransformer import ProgramTransformer
from AST_Scripts.ValidatorProgramVisitors import SimulatorValidator
from AST_Scripts.Retrievers import MatchCounterRetriever
from AST_Scripts.simulator import CoqNVal, Simulator, bit_array_to_int, to_binary_arr
import math
import qiskit
sys.path.append('/Users/anshugsharma/VSCodeRepos/quantumTesting/qiskit-to-xmlprogrammer')
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

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# current_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(current_dir, "PQASM"))

from AST_Scripts.XMLProgrammer import QXProgram, QXQID, QXCU, QXX, QXH, QXRZ, QXRY

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
    transform = ProgramTransformer()
    new_tree = transform.visitRoot(visitor.startVisit(qcEx1, circuitName="Example Circuit 1", optimiseCircuit=True, showDecomposedCircuit=True))

    return new_tree


def get_tree():
    #new_tree = read_program(f"{os.path.dirname(os.path.realpath(__file__))}/mutants/mutant_38.xml")
    new_tree = read_program(f"{os.path.dirname(os.path.realpath(__file__))}/rz_adder_good.xml")

    valid_tree = True

    try:
        # Validation of the Constraints.
        # Added per Dr. Li's suggestion on 11/16 to scoop out the validator behaviour out of the simulator as there can be
        # programs which does not always need to follow constraints like only having 1 app tag.
        validator = SimulatorValidator()
        validator.visitRoot(new_tree)

        # Non-Decreasing Recursive Fixed Point Factor Check
    except Exception as e:
        print('\n ==============', e, '==============')
        valid_tree = False

    retriever = MatchCounterRetriever()
    retriever.visitRoot(new_tree)
    return new_tree, retriever, valid_tree


def run_simulator(n, i, X, M, parseTree):
    val_array = to_binary_arr(X, n)  # Convert value to array
    state = dict({"x": [CoqNVal(val_array, 0)],
                  "size": n,
                  "na": i,
                  "m": M})  # Initial state
    environment = dict({"x": n})  # Environment for simulation

    # Run the Simulator
    y = Simulator(state, environment)
    y.visitRoot(parseTree)
    new_state = y.get_state()
    return bit_array_to_int(new_state.get('x')[0].getBits(), n)
 

def test_property_addition_with_edge_case_M(n,i,X,M, parse_tree):
    if parse_tree[2]:
        expected = (X + (M % (2 ** i))) % (2 ** n)
        assert run_simulator(n,i,X,M, parse_tree[0]) == expected
    else :
        assert False

parsetree = get_tree()


from hypothesis import given, strategies as st, assume, settings, HealthCheck


# @st.composite
# def valid_inputs(draw):
#     n = draw(st.sampled_from([8,16,32,64]))
#     i = draw(st.integers(max_value=n)) 
#     X = st.integers()
#     M = st.sampled_from([10,100,1000])
#     return (n,i,X,M, parsetree)
# @given(valid_inputs())
@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(n = st.sampled_from([8,16,32,64]), 
    i = st.integers(min_value=1),
    X = st.integers(min_value=0), 
    M = st.sampled_from([10,100,1000])
)
def test_addition_with_small_i(n, i, X, M, parse_tree):
    # assume((i > 0) and (X > 0) and (M > 0))

    assume (i < n)

    print (f"test_addition_with_small_i(), called with n = {n}, i = {i}, X = {X}, M = {M}")
    if parse_tree[2]:
        expected = (X + (M % (2 ** i))) % (2 ** n)
        assert run_simulator (n, i, X, M, parse_tree[0]) == expected
    else :
        assert False
    
test_addition_with_small_i(parse_tree=parsetree)


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(n = st.sampled_from([8,16,32,64]),
    i = st.integers(min_value=1),
    X = st.sampled_from([32,64]),
    M = st.integers(min_value=10)
)
def test_addition_with_med_i(n,i,X,M,parse_tree):
    assume (i < n)
    print(f"test_addition_with_med_i(): n = {n}, i = {i}, X = {X}, M = {M}")
    if (parse_tree[2]):
        expected = (X + (M %(2 ** i))) % (2 ** n)
        assert run_simulator(n,i,X,M,parse_tree[0]) == expected
    else:
        assert False

test_addition_with_med_i(parse_tree = parsetree)


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(n = st.sampled_from([8,16,32,64]),
    i = st.integers(min_value = 1),
    X = st.integers(min_value=10),
    M = st.sampled_from([0])
)
def test_addition_with_edge_case_M(n,i,X,M,parse_tree):
    
    assume (i < n)
    print(f"test_addition_with_edge_case_M: n = {n}, i = {i}, X = {X}, M = {M}")
    if parse_tree[2]:
        expected = (X + (M % (2 ** i))) % (2 ** n)
        assert run_simulator (n,i,X,M, parse_tree[0]) == expected
    else:
        assert False


test_addition_with_edge_case_M(parse_tree=parsetree)