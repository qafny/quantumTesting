# Ripple-Carry Circuit Specifications

Let:

```text
n = number of qubits in each input register
X = fixed classical integer used by the classical add/subtract circuits
```

All arithmetic is modulo `2^n`.

All integer registers are interpreted in little-endian order unless otherwise stated:

```text
value(r) = Σ r_i 2^i
```

where `r[0]` is the least significant bit.

---

# 1. `rc_adder_add_classical`

## Functional behavior

```text
|y>|0...0> -> |(y + X) mod 2^n>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `y` | `n` | input/result register | No |
| `a[0]` | `1` | carry ancilla | Must return to `0` |
| `a[1:n+1]` | `n` | temporary register for fixed classical value `X` | Must return to `0...0` |

## Input requirements

```text
y = arbitrary n-bit input
a[0] = 0
a[1:n+1] = 0...0
```

## Output behavior

```text
y_out = (y_in + X) mod 2^n
a[0]_out = 0
a[1:n+1]_out = 0...0
```

## Ancilla requirement

```text
n + 1 ancilla qubits
```

## Qubit behavior

The `y` register is modified and stores the result. The ancilla qubits may change during execution, but all ancilla qubits must return to `0` at the end.

## Expected-output rule for QET

Given input:

```text
y = y_in
ancilla = 0...0
```

Expected output:

```text
y = (y_in + X) mod 2^n
ancilla = 0...0
```

---

# 2. `rc_adder_subtract_classical`

## Functional behavior

```text
|y>|0...0> -> |(y - X) mod 2^n>|0...0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `y` | `n` | input/result register | No |
| `a[0]` | `1` | carry/borrow ancilla | Must return to `0` |
| `a[1:n+1]` | `n` | temporary register for fixed classical value `X` | Must return to `0...0` |

## Input requirements

```text
y = arbitrary n-bit input
a[0] = 0
a[1:n+1] = 0...0
```

## Output behavior

```text
y_out = (y_in - X) mod 2^n
a[0]_out = 0
a[1:n+1]_out = 0...0
```

## Ancilla requirement

```text
n + 1 ancilla qubits
```

## Qubit behavior

The `y` register is modified and stores the result. The ancilla qubits may change during execution, but all ancilla qubits must return to `0` at the end.

## Expected-output rule for QET

Given input:

```text
y = y_in
ancilla = 0...0
```

Expected output:

```text
y = (y_in - X) mod 2^n
ancilla = 0...0
```

---

# 3. `rc_adder_add_quantum`

## Functional behavior

```text
|x>|y>|0> -> |x>|(x + y) mod 2^n>|0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `x` | `n` | first input register | Yes |
| `y` | `n` | second input/result register | No |
| `c` | `1` | carry ancilla | Must return to `0` |

## Input requirements

```text
x = arbitrary n-bit input
y = arbitrary n-bit input
c = 0
```

## Output behavior

```text
x_out = x_in
y_out = (x_in + y_in) mod 2^n
c_out = 0
```

## Ancilla requirement

```text
1 ancilla qubit
```

## Qubit behavior

The `x` register is preserved. The `y` register is modified and stores the result. The carry ancilla `c` may change during execution, but it must return to `0` at the end.

## Expected-output rule for QET

Given input:

```text
x = x_in
y = y_in
c = 0
```

Expected output:

```text
x = x_in
y = (x_in + y_in) mod 2^n
c = 0
```

---

# 4. `rc_adder_subtract_quantum`

## Functional behavior

```text
|x>|y>|0> -> |x>|(y - x) mod 2^n>|0>
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `x` | `n` | first input register | Yes |
| `y` | `n` | second input/result register | No |
| `c` | `1` | carry/borrow ancilla | Must return to `0` |

## Input requirements

```text
x = arbitrary n-bit input
y = arbitrary n-bit input
c = 0
```

## Output behavior

```text
x_out = x_in
y_out = (y_in - x_in) mod 2^n
c_out = 0
```

## Ancilla requirement

```text
1 ancilla qubit
```

## Qubit behavior

The `x` register is preserved. The `y` register is modified and stores the result. The carry/borrow ancilla `c` may change during execution, but it must return to `0` at the end.

## Expected-output rule for QET

Given input:

```text
x = x_in
y = y_in
c = 0
```

Expected output:

```text
x = x_in
y = (y_in - x_in) mod 2^n
c = 0
```

