# hypothesis tests for cl_multiply operator.
from antlr4 import InputStream, CommonTokenStream
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0,parent_dir)
sys.path.insert(2, parent_dir+"/AST_Scripts")

from hypothesis import assume, given, strategies as st

from AST_Scripts.XMLExpLexer import XMLExpLexer
from AST_Scripts.XMLExpParser import XMLExpParser
from AST_Scripts.simulator import to_binary_arr, CoqNVal, Simulator, bit_array_to_int


def simulate_cl_mult(x_array_value, y_array_value, result_array_val, num_qubits):
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/cl_mult_good.xml", 'r') as f:
        str = f.read()
    i_stream = InputStream(str)
    lexer = XMLExpLexer(i_stream)
    t_stream = CommonTokenStream(lexer)
    parser = XMLExpParser(t_stream)
    tree = parser.program()
    # print(tree.toStringTree(recog=parser))

    state = dict(
        {"xa": [CoqNVal(x_array_value, 0)],
         "ya": [CoqNVal(y_array_value, 0)],
         "ca": [CoqNVal(0, 0)],
         "result": [CoqNVal(result_array_val, 0)],
         "na": num_qubits,
         })
    environment = dict(
        {"xa": num_qubits,
         "ya": num_qubits,
         "ca": 1,
         "result": num_qubits
         })
    simulator = Simulator(state, environment)
    simulator.visitProgram(tree)
    new_state = simulator.get_state()
    return new_state

@st.composite
def generate_case(draw):
    nbits = draw(st.sampled_from([8,16,32,64]))
    x = draw(st.integers(min_value = 1, max_value = (2**(nbits-1)))) 
    y = draw(st.integers(min_value = 1, max_value = (2**(nbits-1))))
    assume((x*y) < (2**nbits))
    expected = (x * y)%(2 ** nbits)
    return (nbits, x, y, expected)

@given(generate_case())
def test_in_range_multiplication(case):
    
    val_x = case[1]
    val_y = case[2]
    num_qbits = case[0]
    expected = case[3]+1
    print(f"in_range_multiplication: x={val_x}, y={val_y}, nbits={num_qbits}")
    new_state = simulate_cl_mult(val_x, val_y,0, num_qbits)
    assert expected == bit_array_to_int(new_state.get('ya')[0].getBits(), num_qbits)

@given(generate_case())
def test_zero_multiplication(case):
    val_x = case[1]
    val_y = case[2]
    num_qbits = case[0]
    expected = 0
    print(f"zero_multiplication: x={val_x}, y=0")
    new_state = simulate_cl_mult(val_x, 0, 0, num_qbits)
    assert bit_array_to_int(new_state.get('ya')[0].getBits(), num_qbits) == 0
    print(f"zero_multiplication: x = 0, y = {val_y}")
    new_state = simulate_cl_mult(0, val_y, 0, num_qbits)
    assert bit_array_to_int(new_state.get('ya')[0].getBits(), num_qbits) == 0
    

@st.composite
def generate_case_2(draw):
    # test for negative multiplication.
    nbits = draw(st.sampled_from([8,16,32,40,48,56]))
    x = draw(st.integers(min_value = -(2**nbits), max_value = (2**nbits)-1))
    if (x < 0):
        x = 2**nbits + x
    y = draw(st.integers(min_value = -(2**nbits), max_value = (2**nbits)-1))
    
def test_negative_multiplication(case):
    num_qbits = case[0]
    val_x = case[1]
    val_y = case[2]
    expected = case[3]

test_in_range_multiplication()
# test_zero_multiplication()