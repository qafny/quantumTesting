"""Helpers for generating random programs of a specific (qubits, gates) size.
Wraps existing generate_random_programs so scaling tests produce family of circuits 
"""

import json
import random
from pathlib import Path
from typing import Dict, List

from program_generator.generators.random_circuit_generator import (
    generate_random_programs,
)

DEFAULT_GENERATION_GATES = ["x", "rz", "cx", "ccx"]

def generate_scaling_programs(
    num_qubits: int,
    num_gates: int,
    n_samples: int = 3,
    seed: int = 42,
    generation_gates: List[str] = None,
):
    if generation_gates is None:
        generation_gates = list(DEFAULT_GENERATION_GATES)
    return generate_random_programs(
        num_qubits=num_qubits,
        num_gates=num_gates,
        generation_gates=generation_gates,
        n_samples=n_samples,
        seed=seed,
    )

def generate_random_inputs(
    num_qubits: int,
    count: int,
    seed: int,
) -> List[Dict[str, bool]]:
    rng = random.Random(seed)
    return [
        {str(i): bool(rng.getrandbits(1)) for i in range(num_qubits)}
        for _ in range(count)
    ]

def program_to_python_source(
    program,
    circuit_var_name: str = "circuit",
) -> str:
    from qiskit import qasm2

    qasm = qasm2.dumps(program.circuit)
    return (
        "from qiskit import QuantumCircuit, qasm2\n"
        "\n"
        f"_QASM = {qasm!r}\n"
        f"{circuit_var_name} = qasm2.loads(_QASM)\n"
    )

def write_benchmark(
    output_dir: Path,
    circuit_id: str,
    program,
    inputs: List[Dict[str, bool]],
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    circuit_file = f"{circuit_id}.py"
    inputs_file = f"{circuit_id}_input.json"
    (output_dir / circuit_file).write_text(
        program_to_python_source(program), encoding="utf-8")
    (output_dir / inputs_file).write_text(
        json.dumps(inputs), encoding="utf-8")

    config = {
        "type": "custom",
        "circuits": {
            circuit_id: {
                "circuit_file": circuit_file,
                "circuit_name": "circuit",
                "inputs": {
                    "type": "json",
                    "inputs_file": inputs_file,
                },
                "generation": {
                    "num_qubits": program.num_qubits,
                    "num_gates": program.num_gates,
                    "seed": program.seed,
                    "generation_gates": list(program.generation_gates),
                    "inputs_count": len(inputs),
                },
            }
        },
    }
    (output_dir / ".config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8")
    return output_dir