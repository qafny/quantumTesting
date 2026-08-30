from compiler_testing.reporting.result_models import TranspilerTestResult


def print_result(result: TranspilerTestResult) -> None:
    print(
        f"[{result.status}] "
        f"sample={result.sample_id}, "
        f"seed={result.seed}, "
        f"basis={result.basis_set_name}, "
        f"num_qubits={result.num_qubits}, "
        f"num_gates={result.num_gates}"
    )

    print(f"  original_ops:   {result.original_ops}")
    print(f"  transpiled_ops: {result.transpiled_ops}")

    if not result.basis_passed:
        print(f"  unexpected_ops: {sorted(result.unexpected_ops)}")

    if not result.equivalence_passed:
        print(f"  equivalence: {result.equivalence_reason}")

    print()


def print_summary(results: list[TranspilerTestResult]) -> None:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed

    basis_failed = sum(1 for result in results if not result.basis_passed)
    equivalence_failed = sum(1 for result in results if not result.equivalence_passed)

    unexpected_seen = sorted(
        set().union(*(result.unexpected_ops for result in results))
        if results
        else set()
    )

    print("=" * 80)
    print("Summary")
    print(f"  total:              {total}")
    print(f"  passed:             {passed}")
    print(f"  failed:             {failed}")
    print(f"  basis_failed:       {basis_failed}")
    print(f"  equivalence_failed: {equivalence_failed}")

    if unexpected_seen:
        print(f"  unexpected gates:   {unexpected_seen}")