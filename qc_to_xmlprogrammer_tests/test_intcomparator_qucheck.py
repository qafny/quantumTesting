"""Test IntegerComparatorProperty with QuCheck"""
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

properties_dir = os.path.join(current_dir, 'qucheck_properties')
backend = AerSimulator(method='statevector')
coordinator = Coordinator(num_inputs=10, random_seed=42, alpha=0.01, backend=backend)

print('=' * 80)
print('Testing IntegerComparatorProperty')
print('=' * 80)

try:
    stats = coordinator.test_property(
        path=properties_dir,
        property_name='IntegerComparatorProperty',
        measurements=1000,
        run_optimization=True
    )
    
    print(f'\nResults:')
    print(f'  Circuits executed: {stats.number_circuits_executed}')
    print(f'  Failed: {len(stats.failed_property)}')
    if stats.failed_property:
        print('  Status: ❌ FAILED')
        for prop in stats.failed_property:
            print(f'    - {prop.property.__class__.__name__}')
    else:
        print('  Status: ✅ PASSED')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()


