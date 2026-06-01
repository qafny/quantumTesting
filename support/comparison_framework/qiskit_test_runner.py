#!/usr/bin/env python3
"""
Qiskit Test Runner - Runs circuits through Qiskit's simulators.

This module tests Qiskit circuits using:
- StatevectorSimulator: For exact state vector computation
- AerSimulator: For measurement sampling
"""

import json
import traceback
import time
import numpy as np
from typing import Dict, Any, Optional, Tuple
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.primitives import StatevectorSampler
from qiskit_aer import AerSimulator


class QiskitTestRunner:
    """Runs Qiskit circuits through Qiskit simulators and extracts results."""
    
    def __init__(self):
        self.statevector_sampler = StatevectorSampler()
        self.aer_simulator = AerSimulator()
        self.results = []
    
    def get_default_parameters(self, circuit_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default parameters for circuit instantiation."""
        params = {}
        param_info = circuit_info.get('parameters', {})
        
        for param_name, param_data in param_info.items():
            if param_name == 'name':
                continue
            
            default = param_data.get('default')
            annotation = param_data.get('annotation', '')
            
            if default is None:
                if 'int' in str(annotation):
                    if 'num_qubits' in param_name or 'num_state_qubits' in param_name or 'num_variable_qubits' in param_name:
                        params[param_name] = 2
                    elif 'reps' in param_name:
                        params[param_name] = 1
                    else:
                        params[param_name] = 2
                elif 'list' in str(annotation) or 'Sequence' in str(annotation):
                    continue
                elif 'str' in str(annotation):
                    if default is not None:
                        params[param_name] = default
                else:
                    continue
            else:
                params[param_name] = default
        
        return params
    
    def instantiate_circuit(self, circuit_info: Dict[str, Any]) -> Optional[QuantumCircuit]:
        """Instantiate a Qiskit circuit with default parameters."""
        try:
            import importlib
            module_path = circuit_info['module']
            class_name = circuit_info['class_name']
            
            module = importlib.import_module(module_path)
            circuit_class = getattr(module, class_name)
            
            params = self.get_default_parameters(circuit_info)
            
            # Check if it's a BlueprintCircuit
            base_classes = [b.__name__ for b in circuit_class.__bases__]
            if 'BlueprintCircuit' in base_classes:
                circuit = circuit_class(**params)
                if hasattr(circuit, '_build'):
                    circuit._build()
            else:
                circuit = circuit_class(**params)
            
            # Generate unique name
            circuit_name = f"{class_name}_{params.get('num_qubits', params.get('num_state_qubits', params.get('num_variable_qubits', 2)))}"
            circuit.name = circuit_name
            
            return circuit
        except Exception as e:
            return None
    
    def run_statevector_simulation(self, circuit: QuantumCircuit) -> Dict[str, Any]:
        """Run circuit and extract state vector using Statevector."""
        result = {
            "success": False,
            "statevector": None,
            "statevector_array": None,
            "probabilities": None,
            "error": None
        }
        
        try:
            # Use Statevector directly to compute state vector
            statevector = Statevector(circuit)
            result["statevector"] = str(statevector)
            result["statevector_array"] = statevector.data.tolist() if hasattr(statevector.data, 'tolist') else list(statevector.data)
            
            # Calculate probabilities
            probabilities = np.abs(statevector.data) ** 2
            result["probabilities"] = probabilities.tolist()
            
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
            result["error_traceback"] = traceback.format_exc()
        
        return result
    
    def run_measurement_simulation(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[str, Any]:
        """Run circuit through AerSimulator with measurements and extract counts."""
        result = {
            "success": False,
            "counts": None,
            "error": None
        }
        
        try:
            # Add measurements if not present
            measured_circuit = circuit.copy()
            if circuit.num_clbits == 0:
                measured_circuit.measure_all()
            
            # Run simulation
            job = self.aer_simulator.run(measured_circuit, shots=shots)
            aer_result = job.result()
            
            # Extract counts
            counts = aer_result.get_counts(0)
            result["counts"] = dict(counts)
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
            result["error_traceback"] = traceback.format_exc()
        
        return result
    
    def test_circuit(self, circuit_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single circuit through Qiskit simulators."""
        result = {
            "circuit_name": None,
            "class_name": circuit_info.get('class_name'),
            "module": circuit_info.get('module'),
            "status": "FAILED",
            "instantiation": {"success": False, "error": None},
            "statevector_sim": None,
            "measurement_sim": None,
            "circuit_properties": None,
            "execution_time": 0
        }
        
        start_time = time.time()
        
        # Step 1: Instantiate circuit
        try:
            circuit = self.instantiate_circuit(circuit_info)
            if circuit is None:
                result["instantiation"]["error"] = "Failed to instantiate circuit"
                result["execution_time"] = time.time() - start_time
                return result
            
            result["instantiation"]["success"] = True
            result["circuit_name"] = circuit.name
            result["circuit_properties"] = {
                "num_qubits": circuit.num_qubits,
                "num_clbits": circuit.num_clbits,
                "depth": circuit.depth(),
                "size": circuit.size(),
                "num_parameters": circuit.num_parameters
            }
        except Exception as e:
            result["instantiation"]["error"] = str(e)
            result["instantiation"]["error_traceback"] = traceback.format_exc()
            result["execution_time"] = time.time() - start_time
            return result
        
        # Step 2: Run statevector simulation (for small circuits)
        if circuit.num_qubits <= 10:  # Only for small circuits
            result["statevector_sim"] = self.run_statevector_simulation(circuit)
        
        # Step 3: Run measurement simulation
        result["measurement_sim"] = self.run_measurement_simulation(circuit)
        
        # Determine overall status
        if result["instantiation"]["success"]:
            if result["statevector_sim"] and result["statevector_sim"]["success"]:
                result["status"] = "PASSED"
            elif result["measurement_sim"] and result["measurement_sim"]["success"]:
                result["status"] = "PASSED"
            else:
                result["status"] = "PARTIAL"  # Instantiated but simulation failed
        
        result["execution_time"] = time.time() - start_time
        return result
    
    def run_tests(self, circuit_list: list) -> list:
        """Run tests on a list of circuits."""
        results = []
        for circuit_info in circuit_list:
            print(f"Testing {circuit_info.get('class_name')}...")
            result = self.test_circuit(circuit_info)
            results.append(result)
        return results
    
    def save_results(self, results: list, output_file: str):
        """Save results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    # Example usage
    runner = QiskitTestRunner()
    
    # Example circuit info
    test_circuit = {
        "class_name": "QFT",
        "module": "qiskit.circuit.library",
        "parameters": {
            "num_qubits": {"default": 3, "annotation": "int"}
        }
    }
    
    result = runner.test_circuit(test_circuit)
    print(json.dumps(result, indent=2, default=str))

