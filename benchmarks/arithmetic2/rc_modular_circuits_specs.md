# Ripple-Carry Modular Circuit Specifications

Let:

```text
M = modulus
X = fixed classical integer used by the classical modular add/subtract circuits
n = ceil(log2(M))
```

The `n`-qubit data registers can represent values from `0` to `2^n - 1`, but the modular arithmetic circuits are specified only over the valid modular domain:

```text
0 <= value < M
```

Values outside this range are invalid inputs for the modular benchmark unless a test explicitly studies invalid-state behavior.

All integer registers are interpreted in little-endian order unless otherwise stated:

```text
value(r) = Σ r_i 2^i
```

where `r[0]` is the least significant bit.

---

# 1. `rc_adder_add_classical_modular`

## Functional behavior

```text
|y>|0>|0>|0...0> -> |(y + X) mod M>|0>|0>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `y` | `n` | input/result register | No |
| `overflow` | `1` | overflow/work bit | Must return to `0` |
| `correction_flag` | `1` | correction/work flag | Must return to `0` |
| `helper` | `n + 2` | helper/work register | Must return to `0...0` |

## Input requirements

```text
y = valid n-bit encoding of an integer in [0, M - 1]
overflow = 0
correction_flag = 0
helper = 0...0
```

The input value of `y` must satisfy:

```text
0 <= y_in < M
```

## Output behavior

```text
y_out = (y_in + X) mod M
overflow_out = 0
correction_flag_out = 0
helper_out = 0...0
```

## Ancilla/helper requirement

```text
n + 4 total ancilla/helper qubits
```

This consists of:

```text
1 overflow bit
1 correction flag
n + 2 helper qubits
```

## Qubit behavior

```text
y changes and stores the modular addition result.
overflow may change during execution but must return to 0.
correction_flag may change during execution but must return to 0.
helper may change during execution but must return to 0...0.
```

## Expected-output rule for QET

Given input:

```text
y = y_in
all work/helper qubits = 0
```

Expected output:

```text
y = (y_in + X) mod M
all work/helper qubits = 0
```

---

# 2. `rc_adder_subtract_classical_modular`

## Functional behavior

```text
|y>|0>|0>|0...0> -> |(y - X) mod M>|0>|0>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `y` | `n` | input/result register | No |
| `overflow` | `1` | overflow/work bit | Must return to `0` |
| `correction_flag` | `1` | correction/work flag | Must return to `0` |
| `helper` | `n + 2` | helper/work register | Must return to `0...0` |

## Input requirements

```text
y = valid n-bit encoding of an integer in [0, M - 1]
overflow = 0
correction_flag = 0
helper = 0...0
```

The input value of `y` must satisfy:

```text
0 <= y_in < M
```

## Output behavior

```text
y_out = (y_in - X) mod M
overflow_out = 0
correction_flag_out = 0
helper_out = 0...0
```

## Ancilla/helper requirement

```text
n + 4 total ancilla/helper qubits
```

This consists of:

```text
1 overflow bit
1 correction flag
n + 2 helper qubits
```

## Qubit behavior

```text
y changes and stores the modular subtraction result.
overflow may change during execution but must return to 0.
correction_flag may change during execution but must return to 0.
helper may change during execution but must return to 0...0.
```

## Expected-output rule for QET

Given input:

```text
y = y_in
all work/helper qubits = 0
```

Expected output:

```text
y = (y_in - X) mod M
all work/helper qubits = 0
```

---

# 3. `rc_adder_add_quantum_modular`

## Functional behavior

```text
|x>|y>|0>|0>|0...0> -> |x>|(y + x) mod M>|0>|0>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `x` | `n` | input register | Yes |
| `y` | `n` | input/result register | No |
| `overflow` | `1` | overflow/work bit | Must return to `0` |
| `correction_flag` | `1` | correction/work flag | Must return to `0` |
| `helper` | `n + 2` | helper/work register | Must return to `0...0` |

## Input requirements

```text
x = valid n-bit encoding of an integer in [0, M - 1]
y = valid n-bit encoding of an integer in [0, M - 1]
overflow = 0
correction_flag = 0
helper = 0...0
```

The input values must satisfy:

```text
0 <= x_in < M
0 <= y_in < M
```

## Output behavior

```text
x_out = x_in
y_out = (y_in + x_in) mod M
overflow_out = 0
correction_flag_out = 0
helper_out = 0...0
```

## Ancilla/helper requirement

```text
n + 4 total ancilla/helper qubits
```

This consists of:

```text
1 overflow bit
1 correction flag
n + 2 helper qubits
```

## Qubit behavior

```text
x is preserved.
y changes and stores the modular addition result.
overflow may change during execution but must return to 0.
correction_flag may change during execution but must return to 0.
helper may change during execution but must return to 0...0.
```

## Expected-output rule for QET

Given input:

```text
x = x_in
y = y_in
all work/helper qubits = 0
```

Expected output:

```text
x = x_in
y = (y_in + x_in) mod M
all work/helper qubits = 0
```

---

# 4. `rc_adder_subtract_quantum_modular`

## Functional behavior

```text
|x>|y>|0>|0>|0...0> -> |x>|(y - x) mod M>|0>|0>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `x` | `n` | input register | Yes |
| `y` | `n` | input/result register | No |
| `overflow` | `1` | overflow/work bit | Must return to `0` |
| `correction_flag` | `1` | correction/work flag | Must return to `0` |
| `helper` | `n + 2` | helper/work register | Must return to `0...0` |

## Input requirements

```text
x = valid n-bit encoding of an integer in [0, M - 1]
y = valid n-bit encoding of an integer in [0, M - 1]
overflow = 0
correction_flag = 0
helper = 0...0
```

The input values must satisfy:

```text
0 <= x_in < M
0 <= y_in < M
```

## Output behavior

```text
x_out = x_in
y_out = (y_in - x_in) mod M
overflow_out = 0
correction_flag_out = 0
helper_out = 0...0
```

## Ancilla/helper requirement

```text
n + 4 total ancilla/helper qubits
```

This consists of:

```text
1 overflow bit
1 correction flag
n + 2 helper qubits
```

## Qubit behavior

```text
x is preserved.
y changes and stores the modular subtraction result.
overflow may change during execution but must return to 0.
correction_flag may change during execution but must return to 0.
helper may change during execution but must return to 0...0.
```

## Expected-output rule for QET

Given input:

```text
x = x_in
y = y_in
all work/helper qubits = 0
```

Expected output:

```text
x = x_in
y = (y_in - x_in) mod M
all work/helper qubits = 0
```
