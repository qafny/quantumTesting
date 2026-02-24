"""
QuCheck property for AndGate benchmark testing.
Tests that AndGate computes AND correctly.
"""
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import AndGate
from qucheck.property import Property
from qucheck.input_generators.integer import Integer
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class AndGateProperty(Property):
    """Property: AndGate computes AND of input qubits correctly"""
    
    def get_input_generators(self):
        # Generate 3 input bits for 3-variable AND gate
        return [Integer(0, 1), Integer(0, 1), Integer(0, 1)]
    
    def preconditions(self, a, b, c):
        return True
    
    def operations(self, a, b, c):
        # Build circuit with inputs and AndGate
        qc = QuantumCircuit(4, 1)  # 4 qubits, 1 classical bit for measurement
        if a == 1:
            qc.x(0)
        if b == 1:
            qc.x(1)
        if c == 1:
            qc.x(2)
        
        # Apply AndGate (3 inputs, 1 output on qubit 3)
        and_gate = AndGate(num_variable_qubits=3)
        qc.append(and_gate, [0, 1, 2, 3])
        
        # Expected: output should be AND(a, b, c)
        expected_result = 1 if (a == 1 and b == 1 and c == 1) else 0
        
        # Create expected circuit with same structure
        expected_qc = QuantumCircuit(4, 1)
        if expected_result == 1:
            expected_qc.x(3)  # Set output qubit to |1> if expected is 1
        
        # Compare output qubit (3) between actual and expected
        self.statistical_analysis.assert_equal(
            self,
            3, qc,
            3, expected_qc,
            basis=["z"]
        )

