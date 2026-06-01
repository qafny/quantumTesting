#!/usr/bin/env python3
"""
Subset Selector - Selects a manageable subset of circuits for comparison.

Criteria for selection:
- Small circuits (≤ 10 qubits) for state vector comparison
- Circuits that are likely to work in both pipelines
- Mix of circuit types (arithmetic, feature maps, etc.)
"""

import json
from typing import List, Dict, Any


class SubsetSelector:
    """Selects a subset of circuits for comparison testing."""
    
    def __init__(self, discovered_circuits_file: str):
        with open(discovered_circuits_file, 'r') as f:
            self.all_circuits = json.load(f)
    
    def is_small_circuit(self, circuit_info: Dict[str, Any]) -> bool:
        """Check if circuit is small enough for state vector comparison."""
        params = circuit_info.get('parameters', {})
        
        # Check for qubit count parameters
        for param_name in ['num_qubits', 'num_state_qubits', 'num_variable_qubits']:
            if param_name in params:
                param_data = params[param_name]
                default = param_data.get('default')
                if default is not None and default <= 10:
                    return True
                # If no default, we'll use small default (2) which is ≤ 10
                if default is None:
                    return True
        
        return False
    
    def is_likely_workable(self, circuit_info: Dict[str, Any]) -> bool:
        """Check if circuit is likely to work in both pipelines."""
        class_name = circuit_info.get('class_name', '')
        module = circuit_info.get('module', '')
        
        # Skip abstract/base classes
        if 'BlueprintCircuit' in class_name:
            return False
        
        # Skip circuits with complex parameters we can't handle
        params = circuit_info.get('parameters', {})
        for param_name, param_data in params.items():
            annotation = str(param_data.get('annotation', ''))
            # Skip circuits requiring complex sequences/lists
            if 'Sequence' in annotation and 'complex' in annotation.lower():
                return False
        
        return True
    
    def select_subset(self, max_circuits: int = 20, 
                     prefer_small: bool = True,
                     categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Select a subset of circuits for comparison.
        
        Args:
            max_circuits: Maximum number of circuits to select
            prefer_small: Prefer small circuits (≤ 10 qubits)
            categories: List of categories to include (e.g., ['arithmetic', 'feature_map'])
        """
        selected = []
        candidates = []
        
        for circuit_info in self.all_circuits:
            # Apply filters
            if not self.is_likely_workable(circuit_info):
                continue
            
            # Check category if specified
            if categories:
                module = circuit_info.get('module', '')
                if not any(cat in module.lower() for cat in categories):
                    continue
            
            # Score circuit (higher score = better candidate)
            score = 0
            if prefer_small and self.is_small_circuit(circuit_info):
                score += 10
            
            # Prefer arithmetic circuits (they're well-tested)
            if 'arithmetic' in circuit_info.get('module', ''):
                score += 5
            
            # Prefer circuits with simple parameters
            params = circuit_info.get('parameters', {})
            if len(params) <= 3:
                score += 2
            
            candidates.append((score, circuit_info))
        
        # Sort by score (descending) and select top N
        candidates.sort(key=lambda x: x[0], reverse=True)
        selected = [circuit for _, circuit in candidates[:max_circuits]]
        
        return selected
    
    def get_circuits_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group circuits by category."""
        categories = {
            'arithmetic': [],
            'feature_map': [],
            'n_local': [],
            'data_preparation': [],
            'other': []
        }
        
        for circuit_info in self.all_circuits:
            module = circuit_info.get('module', '').lower()
            
            if 'arithmetic' in module:
                categories['arithmetic'].append(circuit_info)
            elif 'feature' in module:
                categories['feature_map'].append(circuit_info)
            elif 'n_local' in module:
                categories['n_local'].append(circuit_info)
            elif 'data_preparation' in module:
                categories['data_preparation'].append(circuit_info)
            else:
                categories['other'].append(circuit_info)
        
        return categories


if __name__ == "__main__":
    selector = SubsetSelector('benchmarks/discovered_circuits.json')
    
    # Select a subset
    subset = selector.select_subset(max_circuits=15, prefer_small=True)
    
    print(f"Selected {len(subset)} circuits:")
    for circuit in subset:
        print(f"  - {circuit.get('class_name')} ({circuit.get('module')})")
    
    # Save subset
    with open('comparison_framework/results/selected_subset.json', 'w') as f:
        json.dump(subset, f, indent=2)











