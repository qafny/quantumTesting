import json
import os
import importlib
from typing import Dict


def get_default_parameters(circuit_info: Dict):
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


def read_benchmark(benchmark_folder: str):
    circuits_file_path = os.path.join(benchmark_folder, "circuits.json")
    if not os.path.exists(circuits_file_path):
        raise Exception(f"Circuits file not found at {circuits_file_path}")

    with open(circuits_file_path, "r") as circuits_file:
        circuits_json = json.load(circuits_file)

    circuits = []
    for circuit_info in circuits_json:
        try:
            module_path = circuit_info["module"]
            class_name = circuit_info["class_name"]

            module = importlib.import_module(module_path)
            circuit_class = getattr(module, class_name)

            params = get_default_parameters(circuit_info)
            circuit = circuit_class(**params)

            base_classes = [b.__name__ for b in circuit_class.__bases__]
            if 'BlueprintCircuit' in base_classes and hasattr(circuit, '_build'):
                circuit._build()

            circuit.name = f"{class_name}_{params.get('num_qubits', params.get('num_state_qubits', params.get('num_variable_qubits', 2)))}"

            circuits.append(circuit)

        except:
            # TODO: Temporary fix. Remove this
            pass

    return circuits