import json
import random

NUM_QUBITS = 9
N_BITS = 3  
NUM_INPUTS = 30

def int_to_bools(value, nbits): # little endian
    return [(value >> i) & 1 == 1 for i in range(nbits)]

def bools_to_int(bools):
    return sum((1 << i) for i, b in enumerate(bools) if b)

inputs = []
outputs = []

for _ in range(NUM_INPUTS):
    a_val = random.randint(0, (1 << N_BITS) - 1)
    b_val = random.randint(0, (1 << N_BITS) - 1)
    a_bits = int_to_bools(a_val, N_BITS)
    b_bits = int_to_bools(b_val, N_BITS)
    c_bits = int_to_bools(a_val & b_val, N_BITS)
    input_state = {}
    
    for i in range(N_BITS):
        input_state[str(i)] = a_bits[i]
        input_state[str(i + N_BITS)] = b_bits[i]
    for i in range(2*N_BITS, 3*N_BITS):
        input_state[str(i)] = False 
    expected_state = input_state.copy()
    for i in range(N_BITS):
        expected_state[str(2*N_BITS + i)] = c_bits[i]
    inputs.append(input_state)
    outputs.append(expected_state)

with open("bitwise_and_io_inputs.json", "w") as f:
    json.dump(inputs, f, indent=2)
with open("bitwise_and_io_outputs.json", "w") as f:
    json.dump(outputs, f, indent=2)