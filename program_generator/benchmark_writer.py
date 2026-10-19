"""Write generated circuits and inputs in QET's custom benchmark format."""

import json
from pathlib import Path

from generators.inputs import RandomInputGenerator
from program_generator.models.generated_program import GeneratedProgram


def circuit_python_source(program: GeneratedProgram) -> str:
    """Render the recorded gate sequence as a standalone Qiskit program."""
    lines = [
        "from qiskit import QuantumCircuit",
        "",
        f"circuit = QuantumCircuit({program.num_qubits})",
        "",
    ]
    for record in program.gate_sequence:
        gate = record["gate"]
        qubits = record["qubits"]
        params = record["params"]
        if gate in {"x", "h", "s"}:
            line = f"circuit.{gate}({qubits[0]})"
        elif gate == "rz":
            line = f"circuit.rz({repr(params[0])}, {qubits[0]})"
        elif gate in {"cx", "ccx"}:
            line = f"circuit.{gate}({', '.join(map(str, qubits))})"
        elif gate == "mcx":
            line = f"circuit.mcx({record['controls']!r}, {record['target']})"
        else:
            raise ValueError(f"Cannot serialize gate: {gate}")
        lines.append(line)
    return "\n".join(lines) + "\n"


def write_benchmark(
    programs: list[GeneratedProgram], output_dir: str | Path, inputs_per_program: int
) -> Path:
    """Write one config, a Python program, and an input JSON per circuit."""
    if not programs:
        raise ValueError("programs cannot be empty")
    if inputs_per_program <= 0:
        raise ValueError("inputs_per_program must be greater than 0")

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    config = {"type": "custom", "circuits": {}}
    for index, program in enumerate(programs):
        circuit_id = f"circuit_{index:05d}"
        circuit_file = f"{circuit_id}.py"
        inputs_file = f"{circuit_id}_input.json"
        (output_dir / circuit_file).write_text(circuit_python_source(program), encoding="utf-8")
        inputs = RandomInputGenerator(program.num_qubits, inputs_per_program).generate()
        (output_dir / inputs_file).write_text(
            json.dumps(inputs, indent=2) + "\n", encoding="utf-8"
        )
        config["circuits"][circuit_id] = {
            "circuit_file": circuit_file,
            "circuit_name": "circuit",
            "inputs": {"type": "json", "inputs_file": inputs_file},
            "generation": {
                "seed": program.seed,
                "sample_id": program.sample_id,
                "num_qubits": program.num_qubits,
                "num_gates": program.num_gates,
                "generation_gates": list(program.generation_gates),
                "num_h_gates": program.config.num_h_gates,
                "inputs_count": inputs_per_program,
            },
        }

    (output_dir / ".config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    return output_dir