# Consistent gate test workflow

Layout:

- `framework/` — `test_framework.py`, `test_template.py`, this file
- `gate_tests/` — XMLProgrammer gate simulation scripts (`test_*.py`, etc.)
- `qucheck_properties/` — QuCheck property modules
- `run_qucheck_tests.py` / `run_qucheck_tests_simple.py` — QuCheck runners

## New gate test

1. Copy the template into `gate_tests/`:
   - `cp qc_to_xmlprogrammer_tests/framework/test_template.py qc_to_xmlprogrammer_tests/gate_tests/test_MyGate.py`
2. Edit `NUMBER_OF_INPUT_QUBITS`, `build_circuit()`, `validate_result()`.
3. Run:
   - `python qc_to_xmlprogrammer_tests/gate_tests/test_MyGate.py`

## Run many gate tests

From the repo root:

- `python qc_to_xmlprogrammer_tests/run_test_files.py`
- `python qc_to_xmlprogrammer_tests/run_test_files.py --pattern "test_*Gate.py"`

## Try the template

- `python qc_to_xmlprogrammer_tests/framework/test_template.py`
