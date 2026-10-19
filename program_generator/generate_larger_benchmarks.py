"""Generate targeted Python circuits and bounded, unique Boolean inputs."""

import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path

FAMILIES = (
    "single_qubit", "commuting_inverse", "clifford",
    "clifford_t", "separable_unitary", "two_qubit_block",
)


def derived_seed(seed, *parts):
    text = json.dumps([seed, *parts], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def build_inputs(n, limit, rng):
    """Enumerate if small enough; otherwise reserve room for random samples."""
    count = min(limit, 2 ** n)
    if 2 ** n <= limit:
        return [dict(zip(map(str, range(n)), bits))
                for bits in itertools.product((False, True), repeat=n)]

    values, seen = [], set()

    def add(value):
        if value not in seen:
            values.append(value)
            seen.add(value)

    mask = (1 << n) - 1
    structured = [0, mask]
    for q in range(n):
        structured.extend([1 << q, mask ^ (1 << q)])
    structured_budget = min(count, max(2, count // 2))
    for value in structured:
        if len(values) >= structured_budget:
            break
        add(value)
    while len(values) < count:
        add(rng.getrandbits(n))
    return [{str(q): bool((value >> q) & 1) for q in range(n)}
            for value in values]


def block(family, n, rng):
    a = rng.randrange(n)
    angle = lambda: rng.uniform(-2.8, 2.8)
    if family == "single_qubit":
        if rng.randrange(2):
            x, y = angle(), angle()
            return [f"circuit.p({x!r}, {a})", f"circuit.p({y!r}, {a})"]
        return [f"circuit.u({angle()!r}, {angle()!r}, {angle()!r}, {a})"
                for _ in range(2)]
    if family == "clifford_t":
        return [f"circuit.h({a})", f"circuit.t({a})",
                f"circuit.tdg({a})", f"circuit.s({a})"]

    a, b = rng.sample(range(n), 2)
    if family == "commuting_inverse":
        return [f"circuit.cx({a}, {b})", f"circuit.rz({angle()!r}, {a})",
                f"circuit.cx({a}, {b})"]
    if family == "clifford":
        labels = ["".join(rng.choice("IXYZHS") for _ in range(2))
                  for _ in range(2)]
        return [f"circuit.append(Clifford.from_label({label!r}), [{a}, {b}])"
                for label in labels]
    if family == "separable_unitary":
        # One explicit 4x4 UnitaryGate, not two separate one-qubit gates.
        x, y = angle(), angle()
        return [
            f"circuit.append(UnitaryGate(np.kron("
            f"RXGate({x!r}).to_matrix(), RYGate({y!r}).to_matrix())), [{a}, {b}])"
        ]
    if family == "two_qubit_block":
        return [f"circuit.cx({a}, {b})", f"circuit.p({angle()!r}, {b})",
                f"circuit.cx({a}, {b})", f"circuit.cx({a}, {b})",
                f"circuit.u({angle()!r}, {angle()!r}, {angle()!r}, {a})",
                f"circuit.cx({a}, {b})"]
    raise ValueError(f"Unknown family: {family}")


def build_source(family, n, gates, seed):
    if family not in ("single_qubit", "clifford_t") and n < 2:
        raise ValueError(f"{family} requires at least two qubits")
    rng = random.Random(seed)
    lines = [f"circuit.h({q})" for q in range(n)]
    remaining = gates - 2 * n
    patterns = 0
    while remaining:
        next_block = block(family, n, rng)
        if len(next_block) <= remaining:
            lines.extend(next_block)
            remaining -= len(next_block)
            patterns += 1
        else:
            lines.append(f"circuit.x({rng.randrange(n)})")
            remaining -= 1
    lines.extend(f"circuit.h({q})" for q in range(n))
    source = [
        "from qiskit import QuantumCircuit",
        "from qiskit.quantum_info import Clifford",
        "from qiskit.circuit.library import UnitaryGate, RXGate, RYGate",
        "import numpy as np", "", f"circuit = QuantumCircuit({n})", "",
        *lines,
    ]
    return "\n".join(source) + "\n", patterns


def generate(args):
    if any(x <= 0 for x in [*args.num_qubits, *args.num_gates,
                            *args.input_counts, args.circuits_per_family]):
        raise ValueError("All sizes must be positive")
    if len(set(args.families)) != len(args.families):
        raise ValueError("Duplicate families are not allowed")
    for n, gates in itertools.product(args.num_qubits, args.num_gates):
        if gates < 2 * n + 6:
            raise ValueError(f"Use at least {2*n+6} gates for {n} qubits")
        if n < 2 and any(f not in ("single_qubit", "clifford_t") for f in args.families):
            raise ValueError("Selected families require at least two qubits")

    root = Path(args.output_dir)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Use an empty output directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    folders = 0
    for n, gates, input_limit in itertools.product(
        sorted(set(args.num_qubits)), sorted(set(args.num_gates)),
        sorted(set(args.input_counts)),
    ):
        folder = root / f"q{n}_g{gates}_i{input_limit}"
        folder.mkdir()
        config = {"type": "custom", "circuits": {}}
        for family in args.families:
            for sample in range(args.circuits_per_family):
                name = f"{family}_{sample:05d}"
                # Same circuits across input-count sweeps; same input prefixes
                # across circuit-length sweeps for a given qubit count/sample.
                circuit_seed = derived_seed(args.seed, family, n, gates, sample)
                input_seed = derived_seed(args.seed, "input", family, n, sample)
                source, patterns = build_source(family, n, gates, circuit_seed)
                inputs = build_inputs(n, input_limit, random.Random(input_seed))
                (folder / f"{name}.py").write_text(source, encoding="utf-8")
                (folder / f"{name}_input.json").write_text(
                    json.dumps(inputs, indent=2) + "\n", encoding="utf-8")
                config["circuits"][name] = {
                    "circuit_file": f"{name}.py", "circuit_name": "circuit",
                    "inputs": {"type": "json", "inputs_file": f"{name}_input.json"},
                    "generation": {
                        "family": family, "num_qubits": n, "num_gates": gates,
                        "circuit_seed": circuit_seed, "input_seed": input_seed,
                        "target_patterns": patterns, "input_limit": input_limit,
                        "inputs_count": len(inputs),
                    },
                }
        (folder / ".config.json").write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8")
        folders += 1
    print(f"Generated {folders} benchmark folders under {root}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="benchmarks/scaling")
    parser.add_argument("--num-qubits", nargs="+", type=int, default=[4])
    parser.add_argument("--num-gates", nargs="+", type=int, default=[100])
    parser.add_argument("--input-counts", nargs="+", type=int, default=[16])
    parser.add_argument("--circuits-per-family", type=int, default=10)
    parser.add_argument("--families", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    parser.add_argument("--seed", type=int, default=42)
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
