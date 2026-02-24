"""
QuCheck property for XGate benchmark testing.
Tests that X gate flips qubit states correctly.
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate
from qucheck.property import Property
from qucheck.input_generators.integer import Integer
import sys
import os

# Add paths for XMLProgrammer imports
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class XGateProperty(Property):
    """Property: X gate flips |0> to |1> and |1> to |0>"""
    
    def get_input_generators(self):
        # Generate initial qubit state (0 or 1)
        return [Integer(0, 1)]
    
    def preconditions(self, initial_state):
        return True
    
    def operations(self, initial_state):
        # Build circuit with X gate
        qc = QuantumCircuit(1)
        if initial_state == 1:
            qc.x(0)  # Initialize to |1>
        # Apply X gate
        qc.x(0)
        
        # Expected result: opposite of initial state
        expected_qc = QuantumCircuit(1)
        if initial_state == 0:
            expected_qc.x(0)  # Should be |1>
        # else should be |0> (no gate needed)
        
        # Assert that output qubit matches expected
        self.statistical_analysis.assert_equal(
            self, 
            0, qc, 
            0, expected_qc,
            basis=["z"]
        )

