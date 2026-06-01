import json
import os
from typing import List
from matplotlib import pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import StandardEquivalenceLibrary
from qiskit.transpiler import Target

from evaluators.basis import GateSetBasis
from parser.qiskit import QiskitASTParser
from qetast.nodes import QXRoot


def transpile_qiskit_circuit(qc: QuantumCircuit, basis: GateSetBasis, optimization_level: int = 0) -> QuantumCircuit:
    target = Target()

    for gate, props in basis.get_gate_set():
        target.add_instruction(gate, props)

    for gate, props, gate_name in basis.get_custom_gate_definitions():
        target.add_instruction(gate, props, name = gate_name)

    transpiled_qc = transpile(qc, target = target, optimization_level = optimization_level)

    return transpiled_qc


def parse_qiskit_circuit(qc: QuantumCircuit, basis: GateSetBasis) -> QXRoot:
    tqc: QuantumCircuit = transpile_qiskit_circuit(qc, basis)

    ast_parser = QiskitASTParser(tqc)
    return ast_parser.parse()


def read_qiskit_circuit(filename: str, circuit_name: str) -> QuantumCircuit:
    namespace = {}
    with open(filename, "r") as file:
        exec(file.read(), namespace)

    return namespace.get(circuit_name)


def read_qiskit_custom_benchmark(benchmark_folder: str) -> QuantumCircuit:
    config_file_path = os.path.join(benchmark_folder, ".config.json")
    if not os.path.exists(config_file_path):
        raise Exception(f"Config file not found at {config_file_path}")

    with open(config_file_path, "r") as config_file:
        config = json.load(config_file)

    circuit_file_name = config.get("circuit_file", None)
    circuit_name = config.get("circuit_name", None)

    if circuit_name is not None:
        if circuit_name is not None:
            circuit_file_path = os.path.join(benchmark_folder, circuit_file_name)
            return read_qiskit_circuit(circuit_file_path, circuit_name)
        else:
            raise Exception(f"No circuit_name found in config file at {config_file_path}")
    else:
        raise Exception(f"Circuit file not found in the config at {config_file_path}")


def visualize_qiskit_circuit(qc: QuantumCircuit, title: str):
    qc.draw(output="mpl")
    plt.show(title=title)
