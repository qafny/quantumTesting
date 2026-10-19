"""Generate a folder of random QET circuits and their input JSON files.

Run from the project root: python -m program_generator.generate_benchmark ...
"""

import argparse

from program_generator.benchmark_writer import write_benchmark
from program_generator.generators.random_circuit_generator import generate_random_programs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--num-qubits", type=int, required=True)
    parser.add_argument("--num-gates", type=int, required=True)
    parser.add_argument("--generation-gates", nargs="+", required=True)
    parser.add_argument("--num-programs", type=int, required=True)
    parser.add_argument("--inputs-per-program", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True, help="Initial circuit seed")
    parser.add_argument("--num-h-gates", type=int, default=3)
    args = parser.parse_args()

    programs = generate_random_programs(
        num_qubits=args.num_qubits,
        num_gates=args.num_gates,
        generation_gates=args.generation_gates,
        n_samples=args.num_programs,
        seed=args.seed,
        num_h_gates=args.num_h_gates,
    )
    location = write_benchmark(programs, args.output_dir, args.inputs_per_program)
    print(f"Wrote {len(programs)} circuits to {location}")


if __name__ == "__main__":
    main()