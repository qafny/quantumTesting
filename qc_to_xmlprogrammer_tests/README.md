# `qc_to_xmlprogrammer_tests`

- **`gate_tests/`** — Qiskit → XMLProgrammer → simulator scripts (`test_*.py` and related).
- **`framework/`** — Shared helpers (`test_framework.py`), template (`test_template.py`), and `TESTING_TEMPLATE.md`.
- **`qucheck_properties/`** — QuCheck property classes used by the QuCheck runners.
- **`run_test_files.py`** — Runs scripts under `gate_tests/` (see `framework/TESTING_TEMPLATE.md`).
- **`run_qucheck_tests.py`**, **`run_qucheck_tests_simple.py`** — Run QuCheck against `qucheck_properties/`.
