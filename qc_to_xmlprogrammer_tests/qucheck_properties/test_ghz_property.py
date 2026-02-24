"""
QuCheck property for GHZ state benchmark testing.
Tests that GHZ circuit creates entangled state.
"""
from qiskit import QuantumCircuit
from qucheck.property import Property
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)
sys.path.append(parent_dir + '/qiskit-to-xmlprogrammer')


class GHZProperty(Property):
    """Property: GHZ state should have all qubits equal when measured"""
    
    def get_input_generators(self):
        # QuCheck requires at least one input generator, use a dummy
        from qucheck.input_generators.integer import Integer
        return [Integer(0, 0)]  # Always returns 0, not used
    
    def preconditions(self, dummy):
        return True
    
    def operations(self, dummy):
        # Build GHZ circuit: H on first, then CNOTs
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        
        # In GHZ state, all qubits should be equal when measured
        # Check that qubit 0 equals qubit 1
        qc_copy = qc.copy()
        
        self.statistical_analysis.assert_equal(
            self,
            0, qc,
            1, qc_copy,
            basis=["z"]
        )
        
        # Also check qubit 1 equals qubit 2
        qc_copy2 = qc.copy()
        self.statistical_analysis.assert_equal(
            self,
            1, qc,
            2, qc_copy2,
            basis=["z"]
        )

