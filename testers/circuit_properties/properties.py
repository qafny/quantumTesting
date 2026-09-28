"""
Circuit-specific properties
"""

import math
from typing import Any, Dict, List, Optional

from .base import CircuitProperty, PropertyResult


class AddersProperty(CircuitProperty):
    name = "adders"

    _ADDER_CLASS_PATTERNS = (
        "CDKMRippleCarryAdder", "VBERippleCarryAdder", "DraperQFTAdder",
    )

    def applies(self, circuit, circuit_id: str) -> bool:
        cn = circuit.__class__.__name__
        if cn in self._ADDER_CLASS_PATTERNS:
            return True
        cid = (circuit_id or "").lower()
        return any(p.lower() in cid for p in ("cdkm_ripple", "vbe_ripple", "draper_qft"))

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        a_idx = self.find_register(layout, "a")
        b_idx = self.find_register(layout, "b")
        if a_idx is None or b_idx is None:
            return PropertyResult(False, "adder registers a/b not found")
        cin_idx = self.find_register(layout, "cin", "carry_in")
        cout_idx = self.find_register(layout, "cout", "carry_out")
        helper_idx = self.find_register(layout, "helper", "help", "ancilla", "aux")

        kind = self.detect_adder_kind(circuit)
        n = len(a_idx)

        a = self.read_int(ins, a_idx)
        b = self.read_int(ins, b_idx)
        cin = self.read_int(ins, cin_idx) if cin_idx else 0

        total = a + b + cin
        expected_b = total % (2 ** n)
        expected_cout = (total >> n) & 1

        expected = dict(ins)
        self.write_int(expected, b_idx, expected_b)
        if cout_idx is not None:
            self.write_int(expected, cout_idx, expected_cout)

        result = self.check_basis_output(state, expected, num_qubits)
        return result


class IntegerComparatorProperty(CircuitProperty):

    name = "comparator"

    def applies(self, circuit, circuit_id: str) -> bool:
        if circuit.__class__.__name__ == "IntegerComparator":
            return True
        return "integer_comparator" in (circuit_id or "").lower()

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        L = getattr(circuit, "value", None)
        geq = getattr(circuit, "geq", True)
        if L is None:
            return PropertyResult(False, "cannot determine comparison value L")

        layout = self.register_layout(circuit)
        state_idx = self.find_register(layout, "state", "i")
        flag_idx = self.find_register(layout, "compare", "flag", "cmp")
        if state_idx is None or flag_idx is None:
            return PropertyResult(False, "comparator registers not found")

        i_val = self.read_int(ins, state_idx)
        expected_flag = (i_val >= L) if geq else (i_val < L)

        expected = dict(ins)
        self.write_int(expected, flag_idx, int(expected_flag))

        return self.check_basis_output(state, expected, num_qubits)


class MultiplierProperty(CircuitProperty):
    name = "multiplier"

    def applies(self, circuit, circuit_id: str) -> bool:
        cn = circuit.__class__.__name__
        if cn in ("HRSCumulativeMultiplier", "RGQFTMultiplier"):
            return True
        cid = (circuit_id or "").lower()
        return "multiplier" in cid

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        a_idx = self.find_register(layout, "a")
        b_idx = self.find_register(layout, "b")
        out_idx = self.find_register(layout, "out", "z", "result")
        if a_idx is None or b_idx is None or out_idx is None:
            return PropertyResult(False, "multiplier registers not found")

        a = self.read_int(ins, a_idx)
        b = self.read_int(ins, b_idx)
        m = len(out_idx)
        expected_product = (a * b) % (2 ** m)

        expected = dict(ins)
        self.write_int(expected, out_idx, expected_product)

        return self.check_basis_output(state, expected, num_qubits)


class WeightedAdderProperty(CircuitProperty):

    name = "weighted_adder"

    def applies(self, circuit, circuit_id: str) -> bool:
        if circuit.__class__.__name__ == "WeightedAdder":
            return True
        return "weighted_adder" in (circuit_id or "").lower()

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        weights = getattr(circuit, "weights", None)
        if not weights:
            return PropertyResult(False, "weights not available on circuit")

        layout = self.register_layout(circuit)
        state_idx = self.find_register(layout, "state")
        sum_idx = self.find_register(layout, "sum")
        if state_idx is None or sum_idx is None:
            return PropertyResult(False, "weighted adder registers not found")

        expected_sum = 0
        for i, w in enumerate(weights):
            if ins.get(str(state_idx[i]), False):
                expected_sum += int(w)
        expected_sum &= (1 << len(sum_idx)) - 1

        expected = dict(ins)
        self.write_int(expected, sum_idx, expected_sum)

        return self.check_basis_output(state, expected, num_qubits)

class QuadraticFormProperty(CircuitProperty):

    name = "quadratic_form"

    def applies(self, circuit, circuit_id: str) -> bool:
        if circuit.__class__.__name__ == "QuadraticForm":
            return True
        return "quadratic_form" in (circuit_id or "").lower()

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        A = getattr(circuit, "_quadratic", None)
        b = getattr(circuit, "_linear", None)
        c = getattr(circuit, "_offset", None)

        if A is None:
            A = getattr(circuit, "quadratic", None)
        if b is None:
            b = getattr(circuit, "linear", None)
        if c is None:
            c = getattr(circuit, "offset", 0)

        if A is None and b is None:
            return PropertyResult(False, "quadratic form parameters not available")

        import numpy as np
        if A is not None:
            A = np.asarray(A)
        if b is not None:
            b = np.asarray(b)
        if c is None:
            c = 0

        layout = self.register_layout(circuit)
        num_result = len(getattr(circuit, "_result_qubits", []) or []) or (
            circuit.num_qubits - (len(A) if A is not None else len(b)))
        in_idx = list(range(circuit.num_qubits - num_result))
        out_idx = list(range(circuit.num_qubits - num_result, circuit.num_qubits))

        x_bits = [ins.get(str(i), False) for i in in_idx]
        x = sum(b << i for i, b in enumerate(x_bits))

        x_vec = np.array(x_bits, dtype=int)
        val = int(c)
        if b is not None:
            val += int(np.dot(x_vec, b))
        if A is not None:
            val += int(x_vec @ A @ x_vec)

        m = len(out_idx)
        expected_val = val % (2 ** m)

        expected = dict(ins)
        self.write_int(expected, out_idx, expected_val)

        return self.check_basis_output(state, expected, num_qubits)
    

class PauliRotationProperty(CircuitProperty):

    name = "pauli_rotation"

    def applies(self, circuit, circuit_id: str) -> bool:
        cn = circuit.__class__.__name__
        if cn in ("LinearPauliRotations", "PolynomialPauliRotations"):
            return True
        cid = (circuit_id or "").lower()
        return ("linear_pauli_rotations" in cid
                or "polynomial_pauli_rotations" in cid)

    def _angle(self, circuit, x: int) -> Optional[float]:
        cn = circuit.__class__.__name__
        if cn == "LinearPauliRotations":
            slope = getattr(circuit, "slope", 1.0)
            offset = getattr(circuit, "offset", 0.0)
            return slope * x + offset
        if cn == "PolynomialPauliRotations":
            coeffs = getattr(circuit, "coeffs", [0.0, 1.0])
            return sum(c * (x ** i) for i, c in enumerate(coeffs))
        return None

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        state_idx = self.find_register(layout, "state")
        target_idx = self.find_register(layout, "target")
        if state_idx is None or target_idx is None:
            return PropertyResult(False, "pauli rotation registers not found")

        x = self.read_int(ins, state_idx)
        theta = self._angle(circuit, x)
        if theta is None:
            return PropertyResult(False, "could not compute angle")

        p1_expected = math.sin(theta / 2.0) ** 2
        p0_expected = math.cos(theta / 2.0) ** 2

        p0_actual = 0.0
        p1_actual = 0.0
        off_state = 0.0
        target_q = target_idx[0]
        for amp, bits in state:
            in_state = all(
                bits.get(str(i), False) == ins.get(str(i), False)
                for i in state_idx
            )
            if not in_state:
                off_state += abs(amp) ** 2
                continue
            if bits.get(str(target_q), False):
                p1_actual += abs(amp) ** 2
            else:
                p0_actual += abs(amp) ** 2

        tol = 1e-4
        if off_state > tol:
            return PropertyResult(
                False, f"probability off the state register: {off_state:.4f}")
        if abs(p0_actual - p0_expected) > tol:
            return PropertyResult(
                False,
                f"P(|x,0>) = {p0_actual:.4f}, expected {p0_expected:.4f}")
        if abs(p1_actual - p1_expected) > tol:
            return PropertyResult(
                False,
                f"P(|x,1>) = {p1_actual:.4f}, expected {p1_expected:.4f}")
        return PropertyResult(True)


class ExactReciprocalProperty(CircuitProperty):

    name = "exact_reciprocal"

    def applies(self, circuit, circuit_id: str) -> bool:
        if circuit.__class__.__name__ == "ExactReciprocal":
            return True
        return "exact_reciprocal" in (circuit_id or "").lower()

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        state_idx = self.find_register(layout, "state")
        flag_idx = self.find_register(layout, "flag")
        if state_idx is None or flag_idx is None:
            return PropertyResult(False, "exact_reciprocal registers not found")

        scaling = getattr(circuit, "scaling", None)
        if scaling is None:
            return PropertyResult(False, "scaling not available on circuit")

        x = self.read_int(ins, state_idx)
        n = len(state_idx)

        if x == 0:
            s = 0.0
        else:
            s = scaling * (2 ** n) / x
            if s >= 1:
                s = 1.0

        p1_expected = s * s
        p0_expected = 1.0 - p1_expected

        p0_actual = 0.0
        p1_actual = 0.0
        off_state = 0.0
        flag_q = flag_idx[0]
        for amp, bits in state:
            in_state = all(
                bits.get(str(i), False) == ins.get(str(i), False)
                for i in state_idx
            )
            if not in_state:
                off_state += abs(amp) ** 2
                continue
            if bits.get(str(flag_q), False):
                p1_actual += abs(amp) ** 2
            else:
                p0_actual += abs(amp) ** 2

        tol = 1e-4
        if off_state > tol:
            return PropertyResult(
                False, f"probability off the state register: {off_state:.4f}")
        if abs(p0_actual - p0_expected) > tol:
            return PropertyResult(
                False,
                f"P(|x,0>) = {p0_actual:.4f}, expected {p0_expected:.4f}")
        if abs(p1_actual - p1_expected) > tol:
            return PropertyResult(
                False,
                f"P(|x,1>) = {p1_actual:.4f}, expected {p1_expected:.4f}")
        return PropertyResult(True)


class InnerProductProperty(CircuitProperty):

    name = "inner_product"

    def applies(self, circuit, circuit_id: str) -> bool:
        if circuit.__class__.__name__ in ("InnerProduct", "InnerProductGate"):
            return True
        return "inner_product" in (circuit_id or "").lower()

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        n_half = num_qubits // 2
        if n_half * 2 != num_qubits:
            return PropertyResult(False, "circuit does not have 2n qubits")

        x_bits = [ins.get(str(i), False) for i in range(n_half)]
        y_bits = [ins.get(str(i), False) for i in range(n_half, num_qubits)]
        x = sum(b << i for i, b in enumerate(x_bits))
        y = sum(b << i for i, b in enumerate(y_bits))

        dot = bin(x & y).count("1") % 2
        expected_sign = -1.0 if dot else 1.0
        expected_amp = complex(expected_sign, 0.0)

        tol = 1e-6
        found_amp: Optional[complex] = None
        off_prob = 0.0
        for amp, bits in state:
            matches = all(
                bits.get(str(k), False) == ins.get(str(k), False)
                for k in range(num_qubits)
            )
            if matches:
                found_amp = amp
            else:
                off_prob += abs(amp) ** 2

        if found_amp is None:
            return PropertyResult(False, "no amplitude on input basis state")
        if off_prob > tol:
            return PropertyResult(
                False, f"off-target probability {off_prob:.2e}")
        if abs(found_amp - expected_amp) > 10 * tol:
            return PropertyResult(
                False,
                f"amplitude {found_amp} != expected {expected_amp}")

        return PropertyResult(True)


class BitwiseProperty(CircuitProperty):
    name = "bitwise"

    _OPS = {
        "qarithmetic_bitwise_and": "and",
        "qarithmetic_bitwise_or": "or",
        "qarithmetic_bitwise_xor": "xor",
        "qarithmetic_bitwise_not": "not",
    }

    def _which(self, circuit, circuit_id: str) -> Optional[str]:
        if circuit_id in self._OPS:
            return self._OPS[circuit_id]
        name = getattr(circuit, "name", "").lower()
        for key, op in self._OPS.items():
            if key in (circuit_id or "").lower():
                return op
        layout = self.register_layout(circuit)
        if any(k.startswith("c_and") for k in layout):
            return "and"
        if any(k.startswith("c_or") for k in layout):
            return "or"
        if any(k.startswith("c_xor") for k in layout):
            return "xor"
        if any(k.startswith("c_not") for k in layout):
            return "not"
        return None

    def applies(self, circuit, circuit_id: str) -> bool:
        return self._which(circuit, circuit_id) is not None

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        op = self._which(circuit, circuit_id)
        if op is None:
            return PropertyResult(False, "unknown bitwise operation")

        layout = self.register_layout(circuit)
        a_idx = self.find_register(layout, "a_and", "a_or", "a_xor", "a_not", "a")
        c_idx = self.find_register(layout, "c_and", "c_or", "c_xor", "c_not", "c")
        b_idx = None
        if op != "not":
            b_idx = self.find_register(layout, "b_and", "b_or", "b_xor", "b")

        if a_idx is None or c_idx is None or (op != "not" and b_idx is None):
            return PropertyResult(False, "bitwise registers not found")

        expected = dict(ins)
        for i in range(len(a_idx)):
            ab = ins.get(str(a_idx[i]), False)
            if op == "not":
                self.write_int_bit(expected, c_idx[i], not ab)
            else:
                bb = ins.get(str(b_idx[i]), False)
                if op == "and":
                    val = ab and bb
                elif op == "or":
                    val = ab or bb
                else:
                    val = bool(ab) ^ bool(bb)
                self.write_int_bit(expected, c_idx[i], val)

        return self.check_basis_output(state, expected, num_qubits)

    @staticmethod
    def write_int_bit(bits: Dict[str, bool], idx: int, val: bool) -> None:
        bits[str(idx)] = bool(val)


class ShiftProperty(CircuitProperty):
    name = "cyclic_shift"

    _IDS = (
        "qarithmetic_lshift", "qarithmetic_rshift",
        "qarithmetic_controlled_lshift", "qarithmetic_controlled_rshift",
    )

    def _which(self, circuit, circuit_id: str) -> Optional[str]:
        for key in self._IDS:
            if key in (circuit_id or "").lower():
                return key
        layout = self.register_layout(circuit)
        if "a_lshift" in layout:
            return "qarithmetic_lshift"
        if "a_rshift" in layout:
            return "qarithmetic_rshift"
        if "a_controlled_lshift" in layout:
            return "qarithmetic_controlled_lshift"
        if "a_controlled_rshift" in layout:
            return "qarithmetic_controlled_rshift"
        return None

    def applies(self, circuit, circuit_id: str) -> bool:
        return self._which(circuit, circuit_id) is not None

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        which = self._which(circuit, circuit_id)
        if which is None:
            return PropertyResult(False, "unknown shift operation")
        layout = self.register_layout(circuit)

        controlled = "controlled" in which
        left = "lshift" in which
        if controlled:
            ctrl_idx = self.find_register(layout, "control_lshift", "control_rshift", "control")
            a_idx = self.find_register(layout, "a_controlled_lshift", "a_controlled_rshift")
        else:
            ctrl_idx = None
            a_idx = self.find_register(layout, "a_lshift", "a_rshift")
        if a_idx is None:
            return PropertyResult(False, "shift register 'a' not found")

        apply_shift = True
        if controlled and ctrl_idx is not None:
            apply_shift = bool(ins.get(str(ctrl_idx[0]), False))

        a_bits = [ins.get(str(i), False) for i in a_idx]
        n = len(a_bits)
        expected_a: List[bool]
        if not apply_shift:
            expected_a = list(a_bits)
        elif left:
            expected_a = [a_bits[(i + 1) % n] for i in range(n)]
        else:
            expected_a = [a_bits[(i - 1) % n] for i in range(n)]

        expected = dict(ins)
        for i in range(n):
            expected[str(a_idx[i])] = expected_a[i]

        return self.check_basis_output(state, expected, num_qubits)


class RcAdderProperty(CircuitProperty):

    name = "rc_adder"

    _IDS = (
        "rc_adder_add_classical", "rc_adder_subtract_classical",
        "rc_adder_add_quantum", "rc_adder_subtract_quantum",
    )

    def _which(self, circuit, circuit_id: str) -> Optional[str]:
        for key in self._IDS:
            if key in (circuit_id or "").lower():
                return key
        return None

    def applies(self, circuit, circuit_id: str) -> bool:
        return self._which(circuit, circuit_id) is not None

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        which = self._which(circuit, circuit_id)
        if which is None:
            return PropertyResult(False, "unknown RC adder")
        layout = self.register_layout(circuit)

        y_idx = self.find_register(layout, "y")
        if y_idx is None:
            return PropertyResult(False, "RC adder register y not found")
        n = len(y_idx)
        y_in = self.read_int(ins, y_idx)

        expected = dict(ins)
        if which.endswith("_classical"):
            X_VALUE = 9
            if "add_classical" in which:
                y_out = (y_in + X_VALUE) % (2 ** n)
            else:
                y_out = (y_in - X_VALUE) % (2 ** n)
            self.write_int(expected, y_idx, y_out)
        else:
            x_idx = self.find_register(layout, "x")
            if x_idx is None:
                return PropertyResult(False, "RC adder register x not found")
            x_in = self.read_int(ins, x_idx)
            if "add_quantum" in which:
                y_out = (x_in + y_in) % (2 ** n)
            else:
                y_out = (y_in - x_in) % (2 ** n)
            self.write_int(expected, y_idx, y_out)

        return self.check_basis_output(state, expected, num_qubits)


class RcModularProperty(CircuitProperty):
    name = "rc_modular"

    _IDS = (
        "rc_adder_add_classical_modular",
        "rc_adder_subtract_classical_modular",
        "rc_adder_add_quantum_modular",
        "rc_adder_subtract_quantum_modular",
    )

    MODULUS = 5
    X_VALUE = 2

    def _which(self, circuit, circuit_id: str) -> Optional[str]:
        for key in self._IDS:
            if key in (circuit_id or "").lower():
                return key
        return None

    def applies(self, circuit, circuit_id: str) -> bool:
        return self._which(circuit, circuit_id) is not None

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        which = self._which(circuit, circuit_id)
        if which is None:
            return PropertyResult(False, "unknown RC modular circuit")
        layout = self.register_layout(circuit)

        y_idx = None
        x_idx = None
        for name, idx in layout.items():
            if name.startswith("y_"):
                y_idx = idx
            elif name.startswith("x_"):
                x_idx = idx
        if y_idx is None:
            return PropertyResult(False, "y register not found")

        y_in = self.read_int(ins, y_idx)
        M = self.MODULUS

        if "classical" in which:
            if "add" in which:
                y_out = (y_in + self.X_VALUE) % M
            else:
                y_out = (y_in - self.X_VALUE) % M
        else:
            if x_idx is None:
                return PropertyResult(False, "x register not found")
            x_in = self.read_int(ins, x_idx)
            if "add" in which:
                y_out = (y_in + x_in) % M
            else:
                y_out = (y_in - x_in) % M

        expected = dict(ins)
        self.write_int(expected, y_idx, y_out)

        return self.check_basis_output(state, expected, num_qubits)


class AdvancedMultiplyProperty(CircuitProperty):

    name = "advanced_multiply"

    def applies(self, circuit, circuit_id: str) -> bool:
        return circuit_id == "qarithmetic_multiply" or \
               getattr(circuit, "name", "") == "multiply"

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        a_idx = self.find_register(layout, "a_mult")
        b_idx = self.find_register(layout, "b_mult")
        c_idx = self.find_register(layout, "c_mult")
        if a_idx is None or b_idx is None or c_idx is None:
            return PropertyResult(False, "multiply registers not found")

        a = self.read_int(ins, a_idx)
        b = self.read_int(ins, b_idx)
        m = len(c_idx)
        expected_c = (a * b) % (2 ** m)

        expected = dict(ins)
        self.write_int(expected, c_idx, expected_c)

        return self.check_basis_output(state, expected, num_qubits)


class ControlledAdvancedMultiplyProperty(CircuitProperty):
    name = "advanced_controlled_multiply"

    def applies(self, circuit, circuit_id: str) -> bool:
        return circuit_id == "qarithmetic_controlled_multiply" or \
               getattr(circuit, "name", "") == "controlled_multiply"

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        ctrl_idx = self.find_register(layout, "control_cmult")
        a_idx = self.find_register(layout, "a_cmult")
        b_idx = self.find_register(layout, "b_cmult")
        c_idx = self.find_register(layout, "c_cmult")
        if any(i is None for i in (ctrl_idx, a_idx, b_idx, c_idx)):
            return PropertyResult(False, "controlled_multiply registers not found")

        control = self.read_int(ins, ctrl_idx)
        a = self.read_int(ins, a_idx)
        b = self.read_int(ins, b_idx)
        m = len(c_idx)

        if control == 1:
            expected_c = (a * b) % (2 ** m)
        else:
            expected_c = 0

        expected = dict(ins)
        self.write_int(expected, c_idx, expected_c)

        return self.check_basis_output(state, expected, num_qubits)


class AdvancedSquareProperty(CircuitProperty):
    name = "advanced_square"

    def applies(self, circuit, circuit_id: str) -> bool:
        return circuit_id == "qarithmetic_square" or \
               getattr(circuit, "name", "") == "square"

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        a_idx = self.find_register(layout, "a_square")
        b_idx = self.find_register(layout, "b_square")
        if a_idx is None or b_idx is None:
            return PropertyResult(False, "square registers not found")

        a = self.read_int(ins, a_idx)
        m = len(b_idx)
        expected_b = (a * a) % (2 ** m)

        expected = dict(ins)
        self.write_int(expected, b_idx, expected_b)

        return self.check_basis_output(state, expected, num_qubits)


class AdvancedDivideProperty(CircuitProperty):

    name = "advanced_divide"

    def applies(self, circuit, circuit_id: str) -> bool:
        return circuit_id == "qarithmetic_divide" or \
               getattr(circuit, "name", "") == "divide"

    def check(self, circuit, circuit_id: str, ins, state, num_qubits) -> PropertyResult:
        layout = self.register_layout(circuit)
        p_idx = self.find_register(layout, "p_div")
        d_idx = self.find_register(layout, "d_div")
        q_idx = self.find_register(layout, "q_div")
        if any(i is None for i in (p_idx, d_idx, q_idx)):
            return PropertyResult(False, "divide registers not found")

        n = len(q_idx)
        
        dividend = self.read_int(ins, p_idx[:n])
        divisor = self.read_int(ins, d_idx[n:2 * n])

        if divisor == 0:
            return PropertyResult(False, "divide by zero - invalid input")

        quotient = dividend // divisor
        remainder = dividend % divisor

        expected = dict(ins)
        self.write_int(expected, q_idx, quotient)
        self.write_int(expected, p_idx[:n], remainder)
        for i in range(n, 2 * n):
            if i < len(p_idx):
                expected[str(p_idx[i])] = False

        return self.check_basis_output(state, expected, num_qubits)