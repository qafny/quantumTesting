import math
import random
from dataclasses import dataclass
from typing import Callable

from qiskit import QuantumCircuit


GateApplyFn = Callable[[QuantumCircuit, random.Random], dict]


@dataclass(frozen=True)
class GateSpec:
    name: str
    arity: int
    apply: GateApplyFn


def _one_qubit(circuit: QuantumCircuit, rng: random.Random) -> int:
    return rng.randrange(circuit.num_qubits)


def _two_qubits(circuit: QuantumCircuit, rng: random.Random) -> tuple[int, int]:
    if circuit.num_qubits < 2:
        raise ValueError("two-qubit gate requires at least 2 qubits")

    return tuple(rng.sample(range(circuit.num_qubits), 2))

def _mcx_qubits(circuit: QuantumCircuit, rng: random.Random, min_controls: int = 2) -> tuple[list[int], int]:
    if circuit.num_qubits < (min_controls +1) :
        raise ValueError(f"mcx requires at least {min_controls + 1} qubits")

    max_controls = circuit.num_qubits-1
    num_controls = rng.randint(min_controls, max_controls)

    selected = rng.sample(range(circuit.num_qubits), num_controls+1)
    controls = selected[:num_controls]
    target = selected[-1]
    return controls, target

def _three_qubits(circuit: QuantumCircuit, rng: random.Random) -> tuple[int, int, int]:
    if circuit.num_qubits < 3:
        raise ValueError("three-qubit gate requires at least 3 qubits")

    return tuple(rng.sample(range(circuit.num_qubits), 3))


def apply_x(circuit: QuantumCircuit, rng: random.Random) -> dict:
    q = _one_qubit(circuit, rng)
    circuit.x(q)
    return {"gate": "x", "qubits": [q], "params": []}


def apply_h(circuit: QuantumCircuit, rng: random.Random) -> dict:
    q = _one_qubit(circuit, rng)
    circuit.h(q)
    return {"gate": "h", "qubits": [q], "params": []}


def apply_s(circuit: QuantumCircuit, rng: random.Random) -> dict:
    q = _one_qubit(circuit, rng)
    circuit.s(q)
    return {"gate": "s", "qubits": [q], "params": []}


def apply_rz(circuit: QuantumCircuit, rng: random.Random) -> dict:
    q = _one_qubit(circuit, rng)
    theta = rng.uniform(0.0, 2.0 * math.pi)
    circuit.rz(theta, q)
    return {"gate": "rz", "qubits": [q], "params": [theta]}


def apply_cx(circuit: QuantumCircuit, rng: random.Random) -> dict:
    control, target = _two_qubits(circuit, rng)
    circuit.cx(control, target)
    return {"gate": "cx", "qubits": [control, target], "params": []}


def apply_ccx(circuit: QuantumCircuit, rng: random.Random) -> dict:
    control_0, control_1, target = _three_qubits(circuit, rng)
    circuit.ccx(control_0, control_1, target)
    return {"gate": "ccx", "qubits": [control_0, control_1, target], "params": []}

def apply_mcx(circuit: QuantumCircuit, rng: random.Random) -> dict:
    controls, target = _mcx_qubits(circuit, rng)
    circuit.mcx(controls, target)
    return {"gate":"mcx", "qubits": controls + [target], "params": [], "controls":controls, "target":target}

GATE_REGISTRY: dict[str, GateSpec] = {
    "x": GateSpec("x", 1, apply_x),
    "h": GateSpec("h", 1, apply_h),
    "s": GateSpec("s", 1, apply_s),
    "rz": GateSpec("rz", 1, apply_rz),
    "cx": GateSpec("cx", 2, apply_cx),
    "ccx": GateSpec("ccx", 3, apply_ccx),
    "mcx": GateSpec("mcx", -1, apply_mcx)
}


def validate_generation_gates(gates: list[str]) -> None:
    unsupported = set(gates) - set(GATE_REGISTRY.keys())

    if unsupported:
        raise ValueError(
            f"Unsupported generation gates: {sorted(unsupported)}. "
            f"Supported gates: {sorted(GATE_REGISTRY.keys())}"
        )


def get_gate_spec(gate_name: str) -> GateSpec:
    gate_name = gate_name.lower()

    if gate_name not in GATE_REGISTRY:
        raise ValueError(f"Unsupported gate: {gate_name}")

    return GATE_REGISTRY[gate_name]