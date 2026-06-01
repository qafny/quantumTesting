"""
Run QuCheck property-based tests on simple benchmark circuits only.
"""
import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

qucheck_path = os.path.join(parent_dir, 'qucheck')
if os.path.exists(qucheck_path):
    sys.path.insert(0, qucheck_path)

from qucheck.coordinator import Coordinator
from qiskit_aer import AerSimulator

def main():
    properties_dir = os.path.join(current_dir, 'qucheck_properties')
    
    print("=" * 80)
    print("Running QuCheck Tests on Simple Benchmarks (X, Y, RY gates only)")
    print("=" * 80)
    
    backend = AerSimulator(method='statevector')
    coordinator = Coordinator(
        num_inputs=20,  # Fewer inputs for faster testing
        random_seed=42,
        alpha=0.01,
        backend=backend
    )
    
    # Test simple properties
    print("Testing: XGateProperty, YGateProperty, RYGateProperty, IntegerComparatorProperty")
    print("-" * 80)
    
    try:
        # Test specific properties by name
        stats = coordinator.test_property(
            path=properties_dir,
            property_name="XGateProperty",
            measurements=1000,
            run_optimization=True
        )
        
        print(f"\nXGateProperty Results:")
        print(f"  Circuits executed: {stats.number_circuits_executed}")
        print(f"  Failed: {len(stats.failed_property)}")
        
        # Test YGate
        stats = coordinator.test_property(
            path=properties_dir,
            property_name="YGateProperty",
            measurements=1000,
            run_optimization=True
        )
        
        print(f"\nYGateProperty Results:")
        print(f"  Circuits executed: {stats.number_circuits_executed}")
        print(f"  Failed: {len(stats.failed_property)}")
        
        # Test RYGate
        stats = coordinator.test_property(
            path=properties_dir,
            property_name="RYGateProperty",
            measurements=1000,
            run_optimization=True
        )
        
        print(f"\nRYGateProperty Results:")
        print(f"  Circuits executed: {stats.number_circuits_executed}")
        print(f"  Failed: {len(stats.failed_property)}")
        
        # Test IntegerComparator
        stats = coordinator.test_property(
            path=properties_dir,
            property_name="IntegerComparatorProperty",
            measurements=1000,
            run_optimization=True
        )
        
        print(f"\nIntegerComparatorProperty Results:")
        print(f"  Circuits executed: {stats.number_circuits_executed}")
        print(f"  Failed: {len(stats.failed_property)}")
        
        print("\n" + "=" * 80)
        print("Simple tests completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

