import random

from qiskit import QuantumCircuit

from .gate_registry import (
    get_gate_spec,
    validate_generation_gates,
)
from program_generator.models.generated_program import GeneratedProgram
from program_generator.models.generation_config import GenerationConfig


def generate_random_circuit(config: GenerationConfig) -> GeneratedProgram:
    config.validate()

    generation_gates = [gate.lower() for gate in config.generation_gates]
    validate_generation_gates(generation_gates)

    rng = random.Random(config.seed)

    circuit = QuantumCircuit(
        config.num_qubits,
        name=(
            f"random_q{config.num_qubits}"
            f"_g{config.num_gates}"
            f"_s{config.seed}"
            f"_sample{config.sample_id}"
        ),
    )

    gate_sequence: list[dict] = []

    h_count = 0
    max_h_gates = config.num_h_gates

    for gate_index in range(config.num_gates):
        available_gates = list(generation_gates)
        if h_count >= max_h_gates and "h" in available_gates:
            available_gates.remove("h")
        if not available_gates:
            raise ValueError("No available gates left after applying H gate limit")

        gate_name = rng.choice(available_gates)   
        gate_spec = get_gate_spec(gate_name)

        if gate_name == "h":
            h_count += 1

        record = gate_spec.apply(circuit, rng)
        record["index"] = gate_index
        gate_sequence.append(record)

    return GeneratedProgram(
        circuit=circuit,
        config=config,
        original_ops=dict(circuit.count_ops()),
        gate_sequence=gate_sequence,
    )


def generate_random_programs(
    num_qubits: int,
    num_gates: int,
    generation_gates: list[str],
    n_samples: int,
    seed: int,
    num_h_gates: int | None = 3
) -> list[GeneratedProgram]:
    if n_samples <= 0:
        raise ValueError("n_samples must be greater than 0")

    programs: list[GeneratedProgram] = []

    for sample_id in range(n_samples):
        config = GenerationConfig(
            num_qubits=num_qubits,
            num_gates=num_gates,
            generation_gates=generation_gates,
            seed=seed + sample_id,
            sample_id=sample_id,
            num_h_gates=num_h_gates
        )

        programs.append(generate_random_circuit(config))

    return programs