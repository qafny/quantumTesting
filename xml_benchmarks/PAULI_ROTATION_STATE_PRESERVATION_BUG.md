# State Preservation Bug in LinearPauliRotations Transformation

## Issue Summary

The `test_pauli_rotation_state_preservation` test fails because the state qubits are not preserved after simulation. Investigation reveals this is **not a bug in Qiskit**, but rather a **bug in the QCtoXMLProgrammer transformation code** that maps Qiskit qubits to XMLProgrammer AST qubit indices.

## Root Cause

### Problem: Register-Relative vs Global Qubit Indices

The bug is in `qiskit-to-xmlprogrammer/qiskit_to_xmlprogrammer.py` at **line 78**:

```python
# Dictionary mapping Qiskit qubits to XMLProgrammer qubits
self.XMLQubits = dict()
for qubit in self.dag.qubits:
    self.XMLQubits[qubit] = QXNum(qubit._index)  # ❌ BUG: Uses register-relative index
```

### Why This Fails for LinearPauliRotations

`LinearPauliRotations` uses **multiple quantum registers**:
- A `state` register with `num_state_qubits` qubits
- A `target` register with 1 qubit

When Qiskit circuits have multiple registers, `qubit._index` returns the **register-relative index**, not the **global index**:

```
Circuit structure:
- state_0: register="state", _index=0  (first qubit in state register)
- state_1: register="state", _index=1  (second qubit in state register)
- target:  register="target", _index=0  (first qubit in target register) ❌
```

The transformation incorrectly maps:
- `state_0` → `QXNum(0)` ✓ (correct)
- `state_1` → `QXNum(1)` ✓ (correct)
- `target` → `QXNum(0)` ❌ (should be `QXNum(2)`)

### Impact on Circuit Operations

When `LinearPauliRotations` is decomposed, it produces controlled operations like:
```
cx(state_0, target)  →  CX(QXNum(0), QXNum(0))  ❌ Wrong! Both qubits mapped to 0
cx(state_1, target)  →  CX(QXNum(1), QXNum(0))  ❌ Wrong! Target should be 2
```

This causes:
1. **Incorrect qubit targeting**: Operations intended for the target qubit (global index 2) are applied to qubit 0 (state_0)
2. **State corruption**: The state qubits get modified when they shouldn't be
3. **Test failures**: The state preservation property fails because state qubits are being operated on incorrectly

## Evidence

### Decomposed Circuit Structure

When `LinearPauliRotations(num_state_qubits=2)` is transpiled, it produces:
```
Decomposed circuit qubits (global order):
  Global position 0: qubit._index=0  (state_0)
  Global position 1: qubit._index=1  (state_1)
  Global position 2: qubit._index=0  (target - register-relative index!)

Operations:
  0: u on qubits with indices: [0]        (target qubit)
  1: cx on qubits with indices: [0, 0]    ❌ Both show index 0!
  2: ry on qubits with indices: [0]       (target qubit)
  3: cx on qubits with indices: [0, 0]   ❌ Both show index 0!
  4: ry on qubits with indices: [0]       (target qubit)
  5: cx on qubits with indices: [1, 0]    ❌ Target should be 2!
  6: ry on qubits with indices: [0]       (target qubit)
  7: cx on qubits with indices: [1, 0]    ❌ Target should be 2!
```

### Expected vs Actual Behavior

**Expected**: For input state `|x⟩|0⟩`:
- State qubits `|x⟩` should remain unchanged
- Only target qubit should rotate

**Actual**: Due to incorrect qubit mapping:
- Operations intended for target qubit (index 2) are applied to state_0 (index 0)
- State qubits get corrupted
- Test assertion fails: `State qubits not preserved: expected X, got Y`

## Solution

The transformation code should use **global qubit indices** instead of register-relative indices. The fix should be:

```python
# Dictionary mapping Qiskit qubits to XMLProgrammer qubits
self.XMLQubits = dict()
for i, qubit in enumerate(self.dag.qubits):  # Use enumerate for global index
    self.XMLQubits[qubit] = QXNum(i)  # Use global position, not qubit._index
```

This ensures:
- `state_0` → `QXNum(0)` ✓
- `state_1` → `QXNum(1)` ✓
- `target` → `QXNum(2)` ✓

## Affected Circuits

This bug affects **any Qiskit circuit that uses multiple quantum registers**, including:
- `LinearPauliRotations`
- `PolynomialPauliRotations`
- `EvolvedOperatorAnsatz`
- `QAOAAnsatz`
- Any custom circuit with multiple `QuantumRegister` objects

Circuits with a single register (like `cl_adder`, `cl_mult`) work correctly because all qubits have unique register-relative indices that happen to match global indices.

## Test Results

- ✅ `test_cl_adder_property.py`: Passes (single register)
- ✅ `test_cl_mult_property.py`: Passes (single register)
- ✅ `test_rz_adder_property.py`: Passes (single register)
- ❌ `test_pauli_rotation_property.py`: Fails (multiple registers) - **Due to this bug**

## Recommendation

1. **Fix the transformation code** to use global qubit indices (as shown in Solution above)
2. **Re-run the property-based tests** to verify state preservation
3. **Test with other multi-register circuits** to ensure the fix works broadly

## Files Involved

- **Bug location**: `qiskit-to-xmlprogrammer/qiskit_to_xmlprogrammer.py` (line 78)
- **Test file**: `xml_benchmarks/test_pauli_rotation_property.py`
- **Simulator**: `AST_Scripts/simulator.py` (works correctly; receives incorrect qubit indices)

## Additional Notes

- The simulator (`AST_Scripts/simulator.py`) is working correctly
- The Qiskit `LinearPauliRotations` circuit is correct
- The issue is purely in the transformation layer (`QCtoXMLProgrammer`)
- This is a **framework limitation/bug**, not a Qiskit issue















