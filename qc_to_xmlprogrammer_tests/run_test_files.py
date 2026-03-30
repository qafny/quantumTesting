"""Run `gate_tests/test_*.py` scripts from the repo root."""

import argparse
import subprocess
import sys
from pathlib import Path


def discover_tests(base_dir: Path, pattern: str) -> list[Path]:
    return sorted(
        [
            path
            for path in base_dir.glob(pattern)
            if path.is_file() and path.parent == base_dir
        ]
    )


def run_test_file(test_file: Path, root_dir: Path) -> int:
    cmd = [sys.executable, str(test_file)]
    completed = subprocess.run(cmd, cwd=str(root_dir), check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gate_tests/*.py scripts.")
    parser.add_argument(
        "--pattern",
        default="test_*.py",
        help="Glob pattern relative to gate_tests/ (default: test_*.py)",
    )
    args = parser.parse_args()

    package_dir = Path(__file__).resolve().parent
    base_dir = package_dir / "gate_tests"
    root_dir = package_dir.parent
    tests = discover_tests(base_dir, args.pattern)

    if not tests:
        print(f"No tests found for pattern {args.pattern!r} under {base_dir}")
        return 1

    print("=" * 80)
    print(f"Running {len(tests)} test file(s) with pattern: {args.pattern}")
    print("=" * 80)

    failures = []
    for test_file in tests:
        print(f"\n--- Running: {test_file.name} ---")
        code = run_test_file(test_file, root_dir)
        if code != 0:
            failures.append((test_file.name, code))

    print("\n" + "=" * 80)
    if failures:
        print("Some test files failed:")
        for name, code in failures:
            print(f"- {name}: exit code {code}")
        return 1

    print("All test files passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
