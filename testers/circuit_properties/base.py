from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PropertyResult:
    passed: bool
    reason: str = ""
    details: Optional[Dict[str, Any]] = None


class CircuitProperty(ABC):
    name: str = "unnamed"
    description: str = ""

    def applies(self, circuit, circuit_id: str) -> bool:
        return False

    @abstractmethod
    def check(self, circuit, circuit_id: str, ins: Dict[str, bool], state: List, num_qubits: int) -> PropertyResult: ...

    @staticmethod
    def register_layout(circuit) -> Dict[str, List[int]]:
        layout: Dict[str, List[int]] = {}
        for qreg in circuit.qregs:
            layout[qreg.name] = [circuit.find_bit(q).index for q in qreg]
        return layout

    @staticmethod
    def find_register(layout: Dict[str, List[int]], *candidates: str) -> Optional[List[int]]:
        for c in candidates:
            if c in layout:
                return layout[c]
        for c in candidates:
            cl = c.lower()
            for name, idx in layout.items():
                nl = name.lower()
                if nl == cl or nl.startswith(cl):
                    return idx
        return None

    @staticmethod
    def read_int(bits: Dict[str, bool], indices: List[int]) -> int:
        v = 0
        for i, idx in enumerate(indices):
            if bits.get(str(idx), False):
                v |= 1 << i
        return v

    @staticmethod
    def write_int(bits: Dict[str, bool], indices: List[int], value: int) -> None:
        mask = (1 << len(indices)) - 1
        value &= mask
        for i, idx in enumerate(indices):
            bits[str(idx)] = bool((value >> i) & 1)

    @staticmethod
    def check_basis_output(state: List, expected: Dict[str, bool], num_qubits: int, tol: float = 1e-6) -> PropertyResult:
        off_target = 0.0
        target_mag = 0.0
        for amp, bits in state:
            matches = True
            for k in range(num_qubits):
                ks = str(k)
                if bits.get(ks, False) != expected.get(ks, False):
                    matches = False
                    break
            if matches:
                target_mag += abs(amp)
            else:
                off_target += abs(amp) ** 2
        if target_mag < tol:
            return PropertyResult(False, "no amplitude on expected basis state")
        if off_target > tol:
            return PropertyResult(
                False, f"off-target probability {off_target:.2e}")
        if abs(target_mag - 1.0) > tol:
            return PropertyResult(
                False, f"target amplitude magnitude {target_mag:.6f} != 1")
        return PropertyResult(True)

    @staticmethod
    def check_qubits_preserved(state: List, ins: Dict[str, bool], indices: List[int], tol: float = 1e-6) -> PropertyResult:
        off_prob = 0.0
        for amp, bits in state:
            for idx in indices:
                if bits.get(str(idx), False) != ins.get(str(idx), False):
                    off_prob += abs(amp) ** 2
                    break
        if off_prob > tol:
            return PropertyResult(
                False,
                f"probability leaking off preserved subspace: {off_prob:.2e}")
        return PropertyResult(True)

    @staticmethod
    def check_qubits_zero(state: List, indices: List[int], tol: float = 1e-6) -> PropertyResult:
        """
        Check ancilla qubits reset to |0>.
        """
        off_prob = 0.0
        for amp, bits in state:
            for idx in indices:
                if bits.get(str(idx), False):
                    off_prob += abs(amp) ** 2
                    break
        if off_prob > tol:
            return PropertyResult(
                False, f"probability on non-zero ancillas: {off_prob:.2e}")
        return PropertyResult(True)


    @staticmethod
    def has_register(circuit, *prefixes: str) -> bool:
        for qreg in circuit.qregs:
            rn = qreg.name.lower()
            for p in prefixes:
                pn = p.lower()
                if rn == pn or rn.startswith(pn):
                    return True
        return False

    @staticmethod
    def detect_adder_kind(circuit) -> str:
        """
        Full, half or fixed
        """
        has_cin = CircuitProperty.has_register(circuit, "cin", "carry_in")
        has_cout = CircuitProperty.has_register(circuit, "cout", "carry_out")
        if has_cin and has_cout:
            return "full"
        if has_cout:
            return "half"
        return "fixed"