"""
Run QuCheck property-based tests on benchmark circuits.
This script runs QuCheck properties through both Qiskit and XMLProgrammer pipelines.
"""
import sys
import os

# Add paths
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Add qucheck to path
qucheck_path = os.path.join(parent_dir, 'qucheck')
if os.path.exists(qucheck_path):
    sys.path.insert(0, qucheck_path)

from qucheck.coordinator import Coordinator
from qiskit_aer import AerSimulator

def main():
    """Run QuCheck tests on benchmark properties."""
    
    # Properties directory
    properties_dir = os.path.join(current_dir, 'qucheck_properties')
    
    if not os.path.exists(properties_dir):
        print(f"Error: Properties directory not found: {properties_dir}")
        return
    
    print("=" * 80)
    print("Running QuCheck Property-Based Tests on Benchmarks")
    print("=" * 80)
    print(f"Properties directory: {properties_dir}")
    print()
    
    # Create backend
    backend = AerSimulator(method='statevector')
    
    # Create coordinator
    coordinator = Coordinator(
        num_inputs=50,  # Number of test inputs to generate
        random_seed=42,  # For reproducibility
        alpha=0.01,      # Significance level
        backend=backend
    )
    
    # Run tests
    print("Running tests...")
    print("-" * 80)
    
    try:
        stats = coordinator.test(
            path=properties_dir,
            measurements=2000,  # Number of measurements per test
            run_optimization=True,
            number_of_properties=-1  # Test all properties
        )
        
        # Print results
        print()
        print("=" * 80)
        print("Test Results Summary")
        print("=" * 80)
        print(f"Total circuits executed: {stats.number_circuits_executed}")
        print(f"Failed properties: {len(stats.failed_property)}")
        print()
        
        if stats.failed_property:
            print("FAILING PROPERTIES:")
            print("-" * 80)
            coordinator.print_outcomes()
        else:
            print("All properties PASSED!")
            print()
            print("PASSING PROPERTIES:")
            passing = coordinator.test_runner.list_passing_properties()
            for prop in passing:
                print(f"  - {prop.__name__}")
        
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


