#!/usr/bin/env python3
"""
Comparison Runner - Orchestrates running circuits through both pipelines.

This module:
1. Runs circuits through Qiskit simulators (via qiskit_test_runner)
2. Runs circuits through XMLProgrammer pipeline (via existing test_all_benchmarks)
3. Collects and stores results for comparison
"""

import json
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'qiskit-to-xmlprogrammer'))

import sys
import os
framework_dir = os.path.dirname(os.path.abspath(__file__))
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from qiskit_test_runner import QiskitTestRunner
from subset_selector import SubsetSelector

# Import XMLProgrammer testing components
from qiskit_to_xmlprogrammer import QCtoXMLProgrammer
from AST_Scripts.simulator import Simulator, CoqNVal
from AST_Scripts.ValidatorProgramVisitors import SimulatorValidator
from AST_Scripts.Retrievers import MatchCounterRetriever
import io
import contextlib


class XMLProgrammerTestRunner:
    """Runs circuits through the XMLProgrammer pipeline."""
    
    def __init__(self):
        self.visitor = QCtoXMLProgrammer()
    
    def get_default_parameters(self, circuit_info):
        """Generate default parameters (same as test_all_benchmarks.py)."""
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
    
    def instantiate_circuit(self, circuit_info):
        """Instantiate circuit (same as test_all_benchmarks.py)."""
        try:
            import importlib
            module_path = circuit_info['module']
            class_name = circuit_info['class_name']
            
            module = importlib.import_module(module_path)
            circuit_class = getattr(module, class_name)
            
            params = self.get_default_parameters(circuit_info)
            
            base_classes = [b.__name__ for b in circuit_class.__bases__]
            if 'BlueprintCircuit' in base_classes:
                circuit = circuit_class(**params)
                if hasattr(circuit, '_build'):
                    circuit._build()
            else:
                circuit = circuit_class(**params)
            
            circuit_name = f"{class_name}_{params.get('num_qubits', params.get('num_state_qubits', params.get('num_variable_qubits', 2)))}"
            circuit.name = circuit_name
            
            return circuit
        except Exception as e:
            return None
    
    def test_circuit(self, circuit_info):
        """Test circuit through XMLProgrammer pipeline."""
        result = {
            "circuit_name": None,
            "class_name": circuit_info.get('class_name'),
            "module": circuit_info.get('module'),
            "status": "FAILED",
            "instantiation": {"success": False, "error": None},
            "ast_generation": {"success": False, "error": None},
            "validation": {"success": False, "error": None},
            "simulation": {"success": False, "error": None, "state": None},
            "circuit_properties": None,
            "execution_time": 0
        }
        
        import time
        start_time = time.time()
        
        # Step 1: Instantiate
        try:
            circuit = self.instantiate_circuit(circuit_info)
            if circuit is None:
                result["instantiation"]["error"] = "Failed to instantiate"
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
            result["execution_time"] = time.time() - start_time
            return result
        
        # Step 2: Generate AST
        try:
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                ast_tree = self.visitor.startVisit(
                    circuit,
                    circuitName=circuit.name,
                    optimiseCircuit=True,
                    showDecomposedCircuit=False,
                    showInputCircuit=False,
                    emit_xml=False
                )
            result["ast_generation"]["success"] = True
        except Exception as e:
            result["ast_generation"]["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            return result
        
        # Step 3: Validate
        try:
            validator = SimulatorValidator()
            validator.visitProgram(ast_tree)
            result["validation"]["success"] = True
        except Exception as e:
            result["validation"]["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            return result
        
        # Step 4: Simulate
        try:
            state = {
                "test": [CoqNVal([True] + [False] * (circuit.num_qubits - 1), phase=0)]
            }
            environment = {"test": circuit.num_qubits}
            
            simulator = Simulator(state, environment)
            simulator.visitProgram(ast_tree)
            new_state = simulator.get_state()
            
            result["simulation"]["success"] = True
            result["simulation"]["state"] = {
                "register_names": list(new_state.keys()),
                "num_registers": len(new_state)
            }
            result["status"] = "PASSED"
        except Exception as e:
            result["simulation"]["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            return result
        
        result["execution_time"] = time.time() - start_time
        return result


class ComparisonRunner:
    """Orchestrates comparison between Qiskit and XMLProgrammer pipelines."""
    
    def __init__(self, benchmarks_dir: str = None):
        if benchmarks_dir is None:
            benchmarks_dir = os.path.join(parent_dir, 'benchmarks')
        
        self.benchmarks_dir = Path(benchmarks_dir)
        self.discovered_file = self.benchmarks_dir / "discovered_circuits.json"
        self.results_dir = Path(current_dir) / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.qiskit_runner = QiskitTestRunner()
        self.xmlprogrammer_runner = XMLProgrammerTestRunner()
        self.subset_selector = SubsetSelector(str(self.discovered_file))
    
    def select_test_subset(self, max_circuits: int = 15) -> list:
        """Select a subset of circuits for comparison."""
        return self.subset_selector.select_subset(max_circuits=max_circuits, prefer_small=True)
    
    def run_comparison(self, circuit_list: list = None, max_circuits: int = 15) -> dict:
        """Run comparison on a list of circuits."""
        if circuit_list is None:
            circuit_list = self.select_test_subset(max_circuits=max_circuits)
        
        print(f"Running comparison on {len(circuit_list)} circuits...")
        
        comparison_results = {
            "timestamp": datetime.now().isoformat(),
            "total_circuits": len(circuit_list),
            "results": []
        }
        
        for i, circuit_info in enumerate(circuit_list, 1):
            class_name = circuit_info.get('class_name', 'Unknown')
            print(f"\n[{i}/{len(circuit_list)}] Comparing {class_name}...")
            
            comparison_result = {
                "circuit_info": {
                    "class_name": circuit_info.get('class_name'),
                    "module": circuit_info.get('module')
                },
                "qiskit_result": None,
                "xmlprogrammer_result": None,
                "comparison": None
            }
            
            # Run Qiskit pipeline
            try:
                print(f"  Running Qiskit pipeline...")
                comparison_result["qiskit_result"] = self.qiskit_runner.test_circuit(circuit_info)
            except Exception as e:
                comparison_result["qiskit_result"] = {
                    "status": "ERROR",
                    "error": str(e),
                    "error_traceback": traceback.format_exc()
                }
            
            # Run XMLProgrammer pipeline
            try:
                print(f"  Running XMLProgrammer pipeline...")
                comparison_result["xmlprogrammer_result"] = self.xmlprogrammer_runner.test_circuit(circuit_info)
            except Exception as e:
                comparison_result["xmlprogrammer_result"] = {
                    "status": "ERROR",
                    "error": str(e),
                    "error_traceback": traceback.format_exc()
                }
            
            comparison_results["results"].append(comparison_result)
        
        return comparison_results
    
    def save_results(self, results: dict, filename: str = "comparison_results.json"):
        """Save comparison results to JSON file."""
        output_file = self.results_dir / filename
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    runner = ComparisonRunner()
    
    # Run comparison
    results = runner.run_comparison()
    
    # Save results
    runner.save_results(results)
    
    print(f"\nComparison complete! Tested {results['total_circuits']} circuits.")

