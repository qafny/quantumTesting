# QArithmetic Bitwise Circuit Specifications

The four bitwise circuits adapted from the QArithmetic library:

- `qarithmetic_bitwise_and`
- `qarithmetic_bitwise_or`
- `qarithmetic_bitwise_xor`
- `qarithmetic_bitwise_not`

All input and output registers are treated bitwise. Endianness does not change the Boolean relationship because each bit position is processed independently.

---

## General Assumptions

For all four circuits:

- Input registers are preserved.
- Output registers must be initialized to `|0...0>`.
- The output register is part of the functional result, not ancilla.
- There are no separate ancilla/helper qubits.
- These are deterministic basis-state circuits.
- Expected-output testing can compare exact bitstrings.

---

# 1. `qarithmetic_bitwise_and`

## Functional Behavior

```text
|a>|b>|0> -> |a>|b>|a AND b>
```

## Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input, preserved | `n` |
| `c` | output/result | `n` |

## Initial State Requirement

```text
a = arbitrary n-bit input
b = arbitrary n-bit input
c = 0...0
```

## Final State

```text
a_out = a_in
b_out = b_in
c_out[i] = a_in[i] AND b_in[i]
```

for every bit position `i`.


## Gate-Level Implementation Idea

For each bit position `i`:

```text
ccx(a[i], b[i], c[i])
```

Since `c[i]` starts at `0`, the Toffoli gate writes:

```text
c[i] = a[i] AND b[i]
```

## Example

If:

```text
a = 101
b = 110
c = 000
```

then:

```text
c_out = 100
```

because:

```text
1 AND 1 = 1
0 AND 1 = 0
1 AND 0 = 0
```

---

# 2. `qarithmetic_bitwise_or`

## Functional Behavior

```text
|a>|b>|0> -> |a>|b>|a OR b>
```

## Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input, preserved | `n` |
| `c` | output/result | `n` |

## Initial State Requirement

```text
a = arbitrary n-bit input
b = arbitrary n-bit input
c = 0...0
```

## Final State

```text
a_out = a_in
b_out = b_in
c_out[i] = a_in[i] OR b_in[i]
```

for every bit position `i`.


## Gate-Level Implementation Idea

For each bit position `i`, QArithmetic computes OR using:

```text
ccx(a[i], b[i], c[i])
cx(a[i], c[i])
cx(b[i], c[i])
```

This produces:

```text
c[i] = (a[i] AND b[i]) XOR a[i] XOR b[i]
```

For Boolean bits, assuming `c[i]` starts at `0`, this equals:

```text
c[i] = a[i] OR b[i]
```

## Example

If:

```text
a = 101
b = 110
c = 000
```

then:

```text
c_out = 111
```

because:

```text
1 OR 1 = 1
0 OR 1 = 1
1 OR 0 = 1
```

---

# 3. `qarithmetic_bitwise_xor`

## Functional Behavior

```text
|a>|b>|0> -> |a>|b>|a XOR b>
```

## Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `b` | input, preserved | `n` |
| `c` | output/result | `n` |

## Initial State Requirement

```text
a = arbitrary n-bit input
b = arbitrary n-bit input
c = 0...0
```

## Final State

```text
a_out = a_in
b_out = b_in
c_out[i] = a_in[i] XOR b_in[i]
```

for every bit position `i`.

## Gate-Level Implementation Idea

For each bit position `i`:

```text
cx(a[i], c[i])
cx(b[i], c[i])
```

Since `c[i]` starts at `0`, the first CNOT copies `a[i]` into `c[i]`, and the second CNOT XORs `b[i]` into `c[i]`.

So:

```text
c[i] = a[i] XOR b[i]
```

## Example

If:

```text
a = 101
b = 110
c = 000
```

then:

```text
c_out = 011
```

because:

```text
1 XOR 1 = 0
0 XOR 1 = 1
1 XOR 0 = 1
```

---

# 4. `qarithmetic_bitwise_not`

## Functional Behavior

```text
|a>|0> -> |a>|NOT a>
```

## Registers

| Register | Role | Size |
|---|---:|---:|
| `a` | input, preserved | `n` |
| `c` | output/result | `n` |

## Initial State Requirement

```text
a = arbitrary n-bit input
c = 0...0
```

## Final State

```text
a_out = a_in
c_out[i] = NOT a_in[i]
```

for every bit position `i`.

## Gate-Level Implementation Idea

For each bit position `i`:

```text
cx(a[i], c[i])
x(c[i])
```

Since `c[i]` starts at `0`, the CNOT first copies `a[i]` into `c[i]`. Then the `x` gate flips it.

So:

```text
c[i] = NOT a[i]
```

## Example

If:

```text
a = 101
c = 000
```

then:

```text
c_out = 010
```

because:

```text
NOT 1 = 0
NOT 0 = 1
NOT 1 = 0
```

---


# Important Notes

1. The output register must start as `0...0`.
2. The input registers are preserved.
3. There are no separate ancilla/helper qubits.
4. The output register is not ancilla; it is part of the functional result.
5. These circuits are deterministic basis-state circuits, so expected-output testing can compare exact bitstrings.
6. These specs assume the QArithmetic-style implementations used in the benchmark files:
   - `bitwise_and`: one Toffoli per bit.
   - `bitwise_or`: one Toffoli plus two CNOTs per bit.
   - `bitwise_xor`: two CNOTs per bit.
   - `bitwise_not`: one CNOT plus one X gate per bit.
