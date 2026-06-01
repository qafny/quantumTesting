"""
QuCheck property for YGate benchmark testing.
Tests that Y gate works correctly.
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import YGate
from qucheck.property import Property
from qucheck.input_generators.integer import Integer
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class YGateProperty(Property):
    """Property: Y gate applied twice returns to original state"""
    
    def get_input_generators(self):
        return [Integer(0, 1)]
    
    def preconditions(self, initial_state):
        return True
    
    def operations(self, initial_state):
        # Build circuit: initialize, apply Y twice
        qc = QuantumCircuit(1)
        if initial_state == 1:
            qc.x(0)
        qc.y(0)
        qc.y(0)
        
        # Expected: should return to original state
        expected_qc = QuantumCircuit(1)
        if initial_state == 1:
            expected_qc.x(0)
        
        self.statistical_analysis.assert_equal(
            self,
            0, qc,
            0, expected_qc,
            basis=["z"]
        )

