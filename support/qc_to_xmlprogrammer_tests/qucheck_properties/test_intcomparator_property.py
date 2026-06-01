"""
QuCheck property for IntegerComparatorGate benchmark testing.
Tests that IntegerComparatorGate correctly compares input values.
"""
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import IntegerComparatorGate
from qucheck.property import Property
from qucheck.input_generators.integer import Integer
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class IntegerComparatorProperty(Property):
    """
    Property: IntegerComparatorGate correctly sets output qubit to |1> 
    when input value >= comparison value, |0> otherwise.
    
    For 3 state qubits, we can represent values 0-7.
    """
    
    def get_input_generators(self):
        # Generate:
        # 1. Comparison value (0-7, reachable with 3 qubits)
        # 2. Input value (0-7)
        return [Integer(0, 7), Integer(0, 7)]
    
    def preconditions(self, compare_value, input_value):
        return True
    
    def operations(self, compare_value, input_value):
        # Build circuit with IntegerComparatorGate
        # 3 state qubits + 1 output qubit = 4 total qubits
        # Need 4 classical bits to match qubit count for QuCheck measurements
        qc = QuantumCircuit(4, 4)  # 4 qubits, 4 classical bits
        
        # Prepare input state: encode input_value in binary on qubits 0,1,2
        # Convert input_value to binary representation
        for i in range(3):
            if (input_value >> i) & 1:  # Check if bit i is set
                qc.x(i)
        
        # Apply IntegerComparatorGate
        # num_state_qubits=3, value=compare_value, geq=True (default)
        comparator = IntegerComparatorGate(
            num_state_qubits=3, 
            value=compare_value,
            geq=True
        )
        qc.append(comparator, [0, 1, 2, 3])  # State qubits: 0,1,2; Output: 3
        
        # Expected: output qubit (3) should be |1> if input_value >= compare_value
        expected_result = 1 if input_value >= compare_value else 0
        
        # Create expected circuit with same structure (4 qubits, 4 classical bits)
        expected_qc = QuantumCircuit(4, 4)
        if expected_result == 1:
            expected_qc.x(3)  # Set output qubit to |1>
        
        # Compare output qubit (3) between actual and expected
        self.statistical_analysis.assert_equal(
            self,
            3, qc,
            3, expected_qc,
            basis=["z"]
        )

