"""
QuCheck property for RYGate benchmark testing.
Tests that RY gate rotation works correctly.
"""
from qiskit import QuantumCircuit
from qiskit.circuit.library import RYGate
from qucheck.property import Property
from qucheck.input_generators.integer import Integer
import sys
import os
import math

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class RYGateProperty(Property):
    """Property: RY(π) should flip qubit, RY(2π) should return to original"""
    
    def get_input_generators(self):
        # Generate initial state and angle (0=0, 1=π, 2=2π)
        return [Integer(0, 1), Integer(0, 2)]
    
    def preconditions(self, initial_state, angle_choice):
        return True
    
    def operations(self, initial_state, angle_choice):
        angles = {0: 0, 1: math.pi, 2: 2 * math.pi}
        angle = angles[angle_choice]
        
        qc = QuantumCircuit(1)
        if initial_state == 1:
            qc.x(0)
        qc.ry(angle, 0)
        
        # Expected behavior:
        # RY(0): no change
        # RY(π): flips qubit
        # RY(2π): returns to original
        expected_qc = QuantumCircuit(1)
        if angle_choice == 1:  # RY(π) flips
            if initial_state == 0:
                expected_qc.x(0)
        elif angle_choice == 0 or angle_choice == 2:  # RY(0) or RY(2π) no change
            if initial_state == 1:
                expected_qc.x(0)
        
        self.statistical_analysis.assert_equal(
            self,
            0, qc,
            0, expected_qc,
            basis=["z"]
        )

