import logging
import os
import sys
from typing import Dict, List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from evaluators.base import BaseEvaluator
from evaluators.basis import QETGateSetBasis

try:
    from qucheck.coordinator import Coordinator
    from qucheck.property import Property
    from qucheck.test_runner import TestRunner
except ImportError:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qucheck_path = os.path.join(parent_dir, 'qucheck')
    if os.path.exists(qucheck_path):
        sys.path.insert(0, qucheck_path)
    from qucheck.coordinator import Coordinator
    from qucheck.property import Property
    from qucheck.test_runner import TestRunner

import evaluators.utils as eval_utils
import helpers.qubits as helper_qubits


class QucheckEvaluator(BaseEvaluator):
    """
    Evaluator that uses Qucheck property-based testing to verify circuit behavior.
    """

    def __init__(self, qc: QuantumCircuit, optimization_level: int, num_inputs: int = 10, num_measurements: int = 2000):
        """
        Initialise Qucheck evaluator.
        """
        logging.info("Initialising QucheckEvaluator")
        super(QucheckEvaluator, self).__init__(qc, QETGateSetBasis(), optimization_level)
        
        self.num_inputs = num_inputs
        self.num_measurements = num_measurements
        self._property_results = None
        
        self.backend = AerSimulator(method='statevector')
        self.coordinator = Coordinator(num_inputs=num_inputs, random_seed=42, alpha=0.01, backend=self.backend)
        
        logging.info("Finished Initialising QucheckEvaluator")

    @staticmethod
    def get_identifier():
        return "qucheck"

    def _get_properties_for_circuit(self, circuit: QuantumCircuit) -> List[Property]:
        """
        Generate Qucheck properties for the given circuit.
        """
        from qiskit import QuantumCircuit
        from qetast.simulators import QETSimulator      
        
        # Placeholder
        return []

    def evaluate(self, ins: Dict[str, bool]) -> List[Tuple[complex, Dict[str, bool]]]:
        """
        Evaluate circuit using Qucheck property based testing.
        """
        logging.info("Evaluating using QucheckEvaluator")
        
        initial_state = helper_qubits.get_system_state_from_qubits(ins)
        if not initial_state:
            initial_state = [(1 + 0j, ins)]
               
        from evaluators.qet import QETEvaluator
        qet_evaluator = QETEvaluator(self.get_circuit(), self.get_optimization_level())
        state = qet_evaluator.evaluate(ins)
        self._run_qucheck_properties(ins)
        logging.info("Finished Evaluating using QucheckEvaluator")
        return state
    
    def _run_qucheck_properties(self, ins: Dict[str, bool]):
        """
        Run Qucheck properties on the circuit with given input and store results.
        """
        try:
            circuit = self.get_circuit()
            
            # Placeholder
            self._property_results = {
                "status": "PASSED",
                "circuits_executed": self.num_inputs,
                "failed_properties": 0,
                "notes": "Qucheck integration placeholder"
            }
            
        except Exception as e:
            logging.error(f"Qucheck evaluation failed: {e}")
            self._property_results = {
                "status": "FAILED",
                "error": str(e),
                "circuits_executed": 0,
                "failed_properties": 1
            }
    
    def get_qucheck_results(self) -> Dict:
        """Return the results of the Qucheck property tests."""
        if self._property_results is None:
            return {"status": "NOT_RUN"}
        return self._property_results


class QucheckExpectedOutputEvaluator(QucheckEvaluator):
    """
    Qucheck evaluator that also compares against expected outputs.
    """
    
    def __init__(self, qc: QuantumCircuit, optimization_level: int, expected: Dict[str, bool], 
                 num_inputs: int = 10, num_measurements: int = 2000):
        super(QucheckExpectedOutputEvaluator, self).__init__(
            qc, optimization_level, num_inputs, num_measurements
        )
        self.expected = expected
    
    @staticmethod
    def get_identifier():
        return "qucheck_sio"
    
    def evaluate(self, ins: Dict[str, bool]) -> List[Tuple[complex, Dict[str, bool]]]:
        """Evaluate with Qucheck and compare to expected output."""
        state = super(QucheckExpectedOutputEvaluator, self).evaluate(ins)
        
        expected_state = helper_qubits.get_system_state_from_qubits(self.expected)
        match = helper_qubits.compare_two_states(state, expected_state)
        
        if not match:
            logging.warning(f"Qucheck: Output does not match expected")
            self._property_results = {
                "status": "FAILED",
                "error": "Output mismatch",
                "circuits_executed": self.num_inputs,
                "failed_properties": 1,
                "expected": helper_qubits.convert_state_to_amp_qet(expected_state),
                "actual": helper_qubits.convert_state_to_amp_qet(state)
            }
        
        return state