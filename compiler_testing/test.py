from program_generator.generators.random_circuit_generator import generate_random_programs
from compiler_testing.config.basis_sets import BASIS_SET_1, BASIS_SET_2
from compiler_testing.runners.transpiler_test_runner import run_transpiler_tests
from compiler_testing.reporting.summary_printer import print_summary
from qiskit import qasm3


def main():
    programs = generate_random_programs(
        num_qubits=4,
        num_gates=6,
        generation_gates=["mcx"],
        n_samples=1,
        seed=42,
    )
    print(programs[0].circuit)

    results = run_transpiler_tests(
        programs=programs,
        basis_sets=[BASIS_SET_1],
        print_each=True,
    )

    # print_summary(results)

if __name__ == "__main__":
    main()