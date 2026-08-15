# Bitwise Shift Circuit Specifications

Let:

```text
n = number of qubits in the input/output register
```

The shift circuits operate on a single `n`-qubit register `a`. The controlled shift circuits additionally use a one-qubit control register.

All register positions are indexed from `0` to `n - 1`. The specification below describes the transformation at the bit/register level. It does not depend on the internal implementation using `swap` or `cswap` gates.

---

# 1. `lshift`

## Functional behavior

```text
|a> -> |left_shift(a)>
```

This circuit cyclically shifts the register left by one position according to the implemented register-index convention.

For an input register:

```text
a_in = [a_0, a_1, ..., a_{n-2}, a_{n-1}]
```

The output register is:

```text
a_out = [a_1, a_2, ..., a_{n-1}, a_0]
```

Equivalently, for each output bit position `i`:

```text
a_out[i] = a_in[(i + 1) mod n]
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `a` | `n` | input/output register | No |

## Input requirements

```text
a = arbitrary n-bit input
```

There are no output registers that need to be initialized separately.

## Output behavior

```text
a_out[i] = a_in[(i + 1) mod n]
```

## Qubit behavior summary

```text
a is modified in place.
No qubits are preserved position-wise in general.
The transformation is a cyclic permutation of the input bits.
No ancilla qubits are used.
```

---

# 2. `rshift`

## Functional behavior

```text
|a> -> |right_shift(a)>
```

This circuit cyclically shifts the register right by one position according to the implemented register-index convention.

For an input register:

```text
a_in = [a_0, a_1, ..., a_{n-2}, a_{n-1}]
```

The output register is:

```text
a_out = [a_{n-1}, a_0, a_1, ..., a_{n-2}]
```

Equivalently, for each output bit position `i`:

```text
a_out[i] = a_in[(i - 1) mod n]
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `a` | `n` | input/output register | No |

## Input requirements

```text
a = arbitrary n-bit input
```

There are no output registers that need to be initialized separately.

## Output behavior

```text
a_out[i] = a_in[(i - 1) mod n]
```

## Qubit behavior summary

```text
a is modified in place.
No qubits are preserved position-wise in general.
The transformation is a cyclic permutation of the input bits.
No ancilla qubits are used.
```

---

# 3. `controlled_lshift`

## Functional behavior

```text
if control = 1:
    |control>|a> -> |control>|left_shift(a)>
else:
    |control>|a> -> |control>|a>
```

The control qubit determines whether the left shift is applied.

For an input register:

```text
a_in = [a_0, a_1, ..., a_{n-2}, a_{n-1}]
```

If `control_in = 1`, then:

```text
a_out = [a_1, a_2, ..., a_{n-1}, a_0]
```

If `control_in = 0`, then:

```text
a_out = a_in
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `control` | `1` | control input | Yes |
| `a` | `n` | input/output register | Conditionally modified |

## Input requirements

```text
control = 0 or 1
a = arbitrary n-bit input
```

There are no output registers that need to be initialized separately.

## Output behavior

```text
control_out = control_in
```

If `control_in = 1`:

```text
a_out[i] = a_in[(i + 1) mod n]
```

If `control_in = 0`:

```text
a_out[i] = a_in[i]
```

## Qubit behavior summary

```text
control is preserved.
a is modified only when control = 1.
a is unchanged when control = 0.
No ancilla qubits are used.
```

---

# 4. `controlled_rshift`

## Functional behavior

```text
if control = 1:
    |control>|a> -> |control>|right_shift(a)>
else:
    |control>|a> -> |control>|a>
```

The control qubit determines whether the right shift is applied.

For an input register:

```text
a_in = [a_0, a_1, ..., a_{n-2}, a_{n-1}]
```

If `control_in = 1`, then:

```text
a_out = [a_{n-1}, a_0, a_1, ..., a_{n-2}]
```

If `control_in = 0`, then:

```text
a_out = a_in
```

## Registers

| Register | Size | Role | Preserved? |
|---|---:|---|---|
| `control` | `1` | control input | Yes |
| `a` | `n` | input/output register | Conditionally modified |

## Input requirements

```text
control = 0 or 1
a = arbitrary n-bit input
```

There are no output registers that need to be initialized separately.

## Output behavior

```text
control_out = control_in
```

If `control_in = 1`:

```text
a_out[i] = a_in[(i - 1) mod n]
```

If `control_in = 0`:

```text
a_out[i] = a_in[i]
```

## Qubit behavior summary

```text
control is preserved.
a is modified only when control = 1.
a is unchanged when control = 0.
No ancilla qubits are used.
```

---

# Notes

1. These are cyclic shifts, not zero-fill shifts.
2. There are no ancilla or helper qubits in any of the four circuits.
3. The non-controlled circuits modify the input register in place.
4. The controlled circuits preserve the control qubit and conditionally modify the input/output register.
