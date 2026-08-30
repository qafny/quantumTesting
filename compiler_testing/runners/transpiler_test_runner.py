from program_generator.models.generated_program import GeneratedProgram
from compiler_testing.checks.basis_check import check_basis
from compiler_testing.checks.equivalence_check import check_equivalence
from compiler_testing.compiler.transpiler_runner import run_transpiler
from compiler_testing.reporting.result_models import BasisSet, TranspilerTestResult
from compiler_testing.reporting.summary_printer import print_result


def run_transpiler_test_for_program(
    program: GeneratedProgram,
    basis_set: BasisSet,
) -> TranspilerTestResult:
    transpiled_circuit = run_transpiler(program.circuit)

    basis_result = check_basis(
        circuit=transpiled_circuit,
        basis_set=basis_set,
    )

    equivalence_result = check_equivalence(
        original=program.circuit,
        transformed=transpiled_circuit,
    )

    return TranspilerTestResult(
        sample_id=program.sample_id,
        seed=program.seed,
        num_qubits=program.num_qubits,
        num_gates=program.num_gates,
        generation_gates=list(program.generation_gates),
        basis_set_name=basis_set.name,
        original_ops=program.original_ops,
        transpiled_ops=basis_result.transpiled_ops,
        basis_passed=basis_result.passed,
        equivalence_passed=equivalence_result.passed,
        unexpected_ops=basis_result.unexpected_ops,
        equivalence_reason=equivalence_result.reason,
    )


def run_transpiler_tests(
    programs: list[GeneratedProgram],
    basis_sets: list[BasisSet],
    print_each: bool = True,
) -> list[TranspilerTestResult]:
    results: list[TranspilerTestResult] = []

    for basis_set in basis_sets:
        for program in programs:
            result = run_transpiler_test_for_program(
                program=program,
                basis_set=basis_set,
            )

            results.append(result)

            if print_each:
                print_result(result)

    return results