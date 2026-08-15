# Arithmetic Circuit Specifications

For every circuit, the input registers, output registers, ancilla/helper registers, initial-state requirements, final-state requirements, and the mathematical relationship between input and output is defined.


## Global Conventions

All integer registers are interpreted in little-endian order unless stated otherwise.

For an `n`-qubit register `x`:

```text
x = Σ x_i 2^i
```

where `x_0` is the least-significant bit.

For expected-output testing:

```text
input registers  = initialized from generated test cases
output registers = initialized to |0...0> unless otherwise stated
ancilla registers = initialized to |0...0> unless otherwise stated
```

For reversible arithmetic circuits, the expected final condition is usually:

```text
input registers are preserved
output/result registers contain the computed value
ancilla/helper registers return to |0...0>
```

For rotation/amplitude-function circuits, the output is not a deterministic integer register. Those circuits encode a function value into amplitudes or rotations, so expected-output testing must compare amplitudes/probabilities or use a circuit-specific tolerance-based rule.

---


# Qiskit 1.1.0 Library Circuits


## 1. `CDKMRippleCarryAdder`, `kind="fixed"`

### Functional behavior

```text
|a>|b>|helper=0> -> |a>|(a + b) mod 2^n>|helper=0>
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input/result | `n` |
| helper | ancilla/work | `1` |

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 15
```

### Initial state

```text
a      = arbitrary n-bit input
b      = arbitrary n-bit input
helper = 0
```

### Final state

```text
a_out      = a_in
b_out      = (a_in + b_in) mod 2^n
helper_out = 0
```

### Ancilla requirement

```text
1 helper qubit
```

---

## 2 `CDKMRippleCarryAdder`, `kind="half"`

### Functional behavior

```text
|a>|b>|cout=0>|helper=0> -> |a>|sum_low>|cout>|helper=0>
```

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 16
```

### Final relationship

```text
full_sum = a_in + b_in
b_out    = full_sum mod 2^n
cout     = floor(full_sum / 2^n)
```

### Ancilla/work requirement

```text
total overhead = 16 - 2n = 2 qubits for n = 7
```

One overhead qubit is carry-out. The other is helper/work. The helper/work qubit should return to `0`.

---

## 3 `VBERippleCarryAdder`, `kind="fixed"`

### Functional behavior

```text
|a>|b>|ancilla=0> -> |a>|(a + b) mod 2^n>|ancilla=0>
```

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 20
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input/result | `n` |
| helper/work | ancilla | `total_qubits - 2n` |

For `n = 7`:

```text
ancilla/work = 20 - 14 = 6 qubits
```

### Final state

```text
a_out       = a_in
b_out       = (a_in + b_in) mod 2^n
ancilla_out = 0...0
```

---

## 4 `VBERippleCarryAdder`, `kind="half"`

### Functional behavior

```text
|a>|b>|cout=0>|ancilla=0> -> |a>|sum_low>|cout>|ancilla=0>
```

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 21
```

### Final relationship

```text
full_sum = a_in + b_in
b_out    = full_sum mod 2^n
cout     = floor(full_sum / 2^n)
```

### Ancilla/work requirement

For `n = 7`:

```text
total overhead = 21 - 14 = 7 qubits
```

One overhead qubit is carry-out. The remaining overhead qubits are helper/work qubits that should return to `0`.

---

## 5 `VBERippleCarryAdder`, `kind="full"`

### Functional behavior

```text
|cin>|a>|b>|0...0> -> |cin>|a>|(a + b + cin) mod 2^n>|cout>|0...0>
```

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 22
```

### Final relationship

```text
full_sum = a_in + b_in + cin
b_out    = full_sum mod 2^n
cout     = floor(full_sum / 2^n)
```

### Notes

If the generated tests keep `cin = 0`, the full adder reduces to the carry-in-zero case.

---

## 6 `DraperQFTAdder`, `kind="fixed"`

### Functional behavior

```text
|a>|b> -> |a>|(a + b) mod 2^n>
```

### Measured local size

For `num_state_qubits = 7`:

```text
total qubits = 14
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input/result | `n` |

### Initial state

```text
a = arbitrary n-bit input
b = arbitrary n-bit input
```

### Final state

```text
a_out = a_in
b_out = (a_in + b_in) mod 2^n
```

### Ancilla requirement

```text
No ancilla for fixed kind in the measured configuration.
```

---

## 7 `IntegerComparator`, `geq=True`

### Functional behavior

```text
|i>|0>|ancilla=0> -> |i>|i >= L>|ancilla=0>
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `i` | input, preserved | `n` |
| comparison flag | output | `1` |
| helper/work | ancilla | implementation-dependent |

### Measured local size

For `num_state_qubits = 15`:

```text
total qubits = 30
```

### Ancilla requirement

For `n = 15`:

```text
ancilla/work = 30 - 15 - 1 = 14 qubits
```

### Final state

```text
i_out    = i_in
flag_out = 1 iff i_in >= value
ancilla_out = 0...0
```

### Source

Qiskit 1.1.0 `IntegerComparator` documentation.

---

## 8 `IntegerComparator`, `geq=False`

### Functional behavior

```text
|i>|0>|ancilla=0> -> |i>|i < L>|ancilla=0>
```

### Final state

```text
i_out    = i_in
flag_out = 1 iff i_in < value
ancilla_out = 0...0
```

### Ancilla requirement

Same as the `geq=True` comparator for the same `num_state_qubits`.

---

## 9 `WeightedAdder`

### Functional behavior

```text
|q_0 ... q_{n-1}>|0>_sum|0...0>_ancilla
->
|q_0 ... q_{n-1}>|Σ weights[j] * q_j>_sum|0...0>_ancilla
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| state/input | input bits, preserved | `n` |
| sum | weighted-sum output | `s` |
| carry/helper | ancilla/work | implementation-dependent |

### Initial state

```text
state   = arbitrary n-bit bitstring
sum     = 0...0
ancilla = 0...0
```

### Final state

```text
state_out = state_in
sum_out   = Σ weights[j] * state_j
ancilla_out = 0...0
```

If the sum register has width `s`, expected output is:

```text
sum_out = (Σ weights[j] * state_j) mod 2^s
```

### Measured local size

For one tested configuration:

```text
num_state_qubits = 15
weights = [1, 2, ..., 15]
total qubits = 29
```

If the input size is reduced, recompute the register layout and total qubits locally.

---

## 10 `HRSCumulativeMultiplier`

### Functional behavior

```text
|x>|y>|z=0>|aux=0> -> |x>|y>|x*y mod 2^m>|aux=0>
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| `y` | input, preserved | `n` |
| `z` | output/product | `m` |
| `aux` | helper/work | implementation-dependent |

By default:

```text
m = 2n
```

### Initial state

```text
x   = arbitrary n-bit input
y   = arbitrary n-bit input
z   = 0...0
aux = 0...0
```

### Final state

```text
x_out   = x_in
y_out   = y_in
z_out   = (x_in * y_in) mod 2^m
aux_out = 0...0
```

### Ancilla requirement

Implementation-dependent. Must be read from the instantiated circuit using local Qiskit:

```python
print(circuit.qregs)
print(circuit.num_qubits)
print(circuit.num_ancillas)
```

---

## 11 `RGQFTMultiplier`

### Functional behavior

```text
|x>|y>|z=0> -> |x>|y>|x*y mod 2^m>
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| `y` | input, preserved | `n` |
| `z` | output/product | `m` |

### Measured local size

For your tested configuration:

```text
num_state_qubits = 3
num_result_qubits = 6
total qubits = 12
```

Since:

```text
3 + 3 + 6 = 12
```

there is no separate ancilla register in that tested configuration.

### Initial state

```text
x = arbitrary n-bit input
y = arbitrary n-bit input
z = 0...0
```

### Final state

```text
x_out = x_in
y_out = y_in
z_out = (x_in * y_in) mod 2^m
```


---

## 12 `LinearPauliRotations`

### Functional behavior

```text
|x>|0> -> |x>(cos(f(x)/2)|0> + sin(f(x)/2)|1>)
```

where:

```text
f(x) = slope * x + offset
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| target | rotation target/output | `1` |

### Initial state

```text
x      = arbitrary n-bit input
target = 0
```

### Final state

```text
x_out = x_in
target is rotated by angle f(x)
```

### Testing note

This is not a deterministic integer-output circuit. Expected-output testing must compare amplitudes or probabilities, not just final bitstrings.

### Source

Qiskit 1.1.0 `LinearPauliRotations` documentation.

---

## 13 `PolynomialPauliRotations`

### Functional behavior

```text
|x>|0> -> |x>(cos(p(x)/2)|0> + sin(p(x)/2)|1>)
```

where:

```text
p(x) = Σ coeffs[j] * x^j
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| target | rotation target/output | `1` |

### Initial state

```text
target = 0
```

### Final state

```text
x_out = x_in
target is rotated by angle p(x)
```

### Testing note

This is an amplitude/rotation-encoding circuit. Do not test it with integer-output expectations unless the comparator supports amplitude-level expected outputs.

### Source

Qiskit `PolynomialPauliRotations` documentation.

---

## 14 `PiecewiseLinearPauliRotations`

### Functional behavior

```text
|x>|0>|ancilla=0> -> |x>|rotated_target>|ancilla=0>
```

The rotation angle is defined by a piecewise-linear function.

For segment `j`:

```text
f(x) = slopes[j] * x + offsets[j]
```

with the active segment determined by the configured breakpoints.

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| target | rotation target/output | `1` |
| helper/work | ancilla | implementation-dependent |

### Measured local size

For your tested configuration:

```text
num_state_qubits = 8
total qubits = 17
```

Therefore:

```text
ancilla/work = 17 - 8 - 1 = 8 qubits
```

### Initial state

```text
x       = arbitrary 8-bit input
target  = 0
ancilla = 0...0
```

### Final state

```text
x_out = x_in
target is rotated by f(x)
ancilla_out = 0...0
```

### Testing note

This is an amplitude/rotation-encoding circuit. Test amplitudes/probabilities, not integer registers.

### Source

Qiskit 1.1.0 `PiecewiseLinearPauliRotations` documentation.

---

## 15 `LinearAmplitudeFunction`

### Functional behavior

```text
|x>|0> -> |x>|amplitude-encoded f(x)>
```

The function maps values in a configured domain to a configured image interval, with a rescaling factor.

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| target | amplitude target/output | `1` |

### Measured local size

For tested configuration:

```text
num_state_qubits = 8
total qubits = 9
```

Therefore, there is no separate ancilla register in the tested configuration.

### Initial state

```text
x      = arbitrary 8-bit input
target = 0
```

### Final state

```text
x_out = x_in
target amplitude encodes the scaled linear function value
```


---

## 16 `ExactReciprocal`

### Functional behavior

Qiskit defines this as an amplitude-encoding reciprocal circuit.

Conceptually:

```text
|x>|0> -> |x>(cos(s/x)|0> + sin(s/x)|1>)
```

where `s` is the configured scaling factor.

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | input, preserved | `n` |
| target | reciprocal amplitude target | `1` |

### Initial state

```text
x      = nonzero input
target = 0
```

### Final state

```text
x_out = x_in
target amplitudes encode scaling / x
```

### Input restriction

```text
x != 0
```

Avoid zero in generated tests.


---

## 17 `QuadraticForm`

### Functional behavior

```text
|x>|0>_m -> |x>|Q(x) mod 2^m>
```

where:

```text
Q(x) = x^T A x + x^T b + c
```

### Registers

| Register | Role | Size |
|---|---:|---:|
| `x` | binary input variables, preserved | `n` |
| result | output | `m` |

### Tested configuration

```text
input/state qubits = 8
result qubits = 5
total qubits = 13
```

Since:

```text
8 + 5 = 13
```

there is no separate ancilla register in the tested configuration.

### Initial state

```text
x      = arbitrary n-bit input
result = 0...0
```

### Final state

```text
x_out      = x_in
result_out = (x^T A x + x^T b + c) mod 2^m
```

### Ancilla requirement

```text
No separate ancilla in the tested 8-input, 5-result-qubit configuration.
```
