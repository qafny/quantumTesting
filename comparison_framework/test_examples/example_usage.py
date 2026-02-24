#!/usr/bin/env python3
"""
Example usage of the comparison framework.

This script demonstrates how to use the comparison framework components.
"""

import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
framework_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(framework_dir)
sys.path.insert(0, framework_dir)
sys.path.insert(0, parent_dir)

from comparison_framework.subset_selector import SubsetSelector
from comparison_framework.qiskit_test_runner import QiskitTestRunner
from comparison_framework.comparison_runner import ComparisonRunner
from comparison_framework.comparison_analyzer import ComparisonAnalyzer


def example_subset_selection():
    """Example: Select a subset of circuits."""
    print("="*60)
    print("Example: Subset Selection")
    print("="*60)
    
    selector = SubsetSelector('benchmarks/discovered_circuits.json')
    subset = selector.select_subset(max_circuits=5, prefer_small=True)
    
    print(f"\nSelected {len(subset)} circuits:")
    for circuit in subset:
        print(f"  - {circuit.get('class_name')} ({circuit.get('module')})")


def example_qiskit_test():
    """Example: Test a single circuit with Qiskit."""
    print("\n" + "="*60)
    print("Example: Qiskit Test Runner")
    print("="*60)
    
    runner = QiskitTestRunner()
    
    # Example circuit
    test_circuit = {
        "class_name": "QFT",
        "module": "qiskit.circuit.library",
        "parameters": {
            "num_qubits": {"default": 3, "annotation": "int"}
        }
    }
    
    result = runner.test_circuit(test_circuit)
    print(f"\nCircuit: {result.get('circuit_name')}")
    print(f"Status: {result.get('status')}")
    print(f"Qubits: {result.get('circuit_properties', {}).get('num_qubits')}")


def example_full_comparison():
    """Example: Run full comparison (small subset)."""
    print("\n" + "="*60)
    print("Example: Full Comparison")
    print("="*60)
    
    runner = ComparisonRunner()
    results = runner.run_comparison(max_circuits=3)
    
    print(f"\nComparison complete! Tested {results['total_circuits']} circuits.")
    
    # Analyze results
    import tempfile
    import json
    from pathlib import Path
    
    # Save to temp file for analysis
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(results, temp_file, indent=2, default=str)
    temp_file.close()
    
    analyzer = ComparisonAnalyzer(temp_file.name)
    analysis = analyzer.analyze_all()
    
    print(f"\nAnalysis Summary:")
    print(f"  Both Passed: {analysis['summary']['both_passed']}")
    print(f"  Discrepancies: {analysis['summary']['discrepancies']}")
    
    # Cleanup
    os.unlink(temp_file.name)


if __name__ == "__main__":
    print("Comparison Framework Examples")
    print("="*60)
    
    # Run examples
    example_subset_selection()
    example_qiskit_test()
    
    # Uncomment to run full comparison (takes longer)
    # example_full_comparison()
    
    print("\n" + "="*60)
    print("Examples complete!")











