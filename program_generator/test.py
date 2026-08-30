from program_generator.generators.random_circuit_generator import generate_random_programs


def main():
    programs = generate_random_programs(
        num_qubits=5,
        num_gates=20,
        generation_gates=["cx", "x", "h", "rz"],
        n_samples=3,
        seed=42,
        num_h_gates=0
    )

    for program in programs:
        print("=" * 80)
        print(f"sample_id: {program.sample_id}")
        print(f"seed: {program.seed}")
        print(f"ops: {program.original_ops}")
        print(program.circuit)


if __name__ == "__main__":
    main()