# Consistent `test_*.py` Workflow

Use these files to keep all local gate tests consistent:

- `test_framework.py`: shared setup/compile/simulate helpers
- `test_template.py`: copy-and-edit template for new tests
- `run_test_files.py`: runner for all top-level `test_*.py` files

## Create a new test file

1. Copy the template:
   - `cp qc_to_xmlprogrammer_tests/test_template.py qc_to_xmlprogrammer_tests/(for example you can make a file name: test_MyGate.py`
2. Edit:
   - `NUMBER_OF_INPUT_QUBITS`
   - `build_circuit()`
   - `validate_result()`
3. Run a single test:
   - `python qc_to_xmlprogrammer_tests/test_MyGate.py`

## Run all top-level test files

- `python qc_to_xmlprogrammer_tests/run_test_files.py`

## Run a subset by pattern

- `python qc_to_xmlprogrammer_tests/run_test_files.py --pattern "test_*Gate.py"`
