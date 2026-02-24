# Qiskit vs XMLProgrammer Comparison Framework

This framework compares the testing of Qiskit circuit library functions using two different approaches:

1. **Qiskit Pipeline**: Qiskit Circuit → Qiskit Simulators (StatevectorSimulator, AerSimulator)
2. **XMLProgrammer Pipeline**: Qiskit Circuit → QCtoXMLProgrammer → XMLProgrammer AST → Custom Simulator

## Overview

The comparison framework:
- Selects a subset of testable circuits from the Qiskit library
- Runs each circuit through both pipelines
- Compares results (state vectors, measurement probabilities, circuit properties)
- Generates detailed comparison reports (JSON and HTML)

## Structure

```
comparison_framework/
├── README.md                    # This file
├── run_comparison.py            # Main script to run comparison
├── qiskit_test_runner.py        # Runs circuits through Qiskit simulators
├── comparison_runner.py         # Orchestrates both pipelines
├── comparison_analyzer.py       # Analyzes and compares results
├── subset_selector.py           # Selects testable circuit subset
├── results/                     # Output directory
│   ├── comparison_results.json  # Raw comparison results
│   ├── comparison_report.json   # Analysis report (JSON)
│   └── comparison_report.html   # Analysis report (HTML)
└── test_examples/               # Example test files
```

## Usage

### Run Full Comparison

```bash
cd comparison_framework
python run_comparison.py --max-circuits 15
```

Options:
- `--max-circuits N`: Maximum number of circuits to test (default: 15)
- `--output-dir DIR`: Output directory for results (default: `comparison_framework/results`)

### Analyze Existing Results

```bash
python run_comparison.py --analyze-only results/comparison_results.json
```

## Components

### 1. Subset Selector (`subset_selector.py`)

Selects a manageable subset of circuits for comparison:
- Prefers small circuits (≤ 10 qubits) for state vector comparison
- Filters out circuits unlikely to work in both pipelines
- Prioritizes arithmetic circuits (well-tested)

### 2. Qiskit Test Runner (`qiskit_test_runner.py`)

Runs circuits through Qiskit's simulators:
- **StatevectorSimulator**: Extracts exact state vectors (for small circuits)
- **AerSimulator**: Performs measurement sampling
- Handles parameterized circuits
- Records circuit properties (qubits, depth, size)

### 3. XMLProgrammer Test Runner (in `comparison_runner.py`)

Runs circuits through the XMLProgrammer pipeline:
- Instantiates circuits with default parameters
- Converts to XMLProgrammer AST via `QCtoXMLProgrammer`
- Validates AST using `SimulatorValidator`
- Simulates using custom `Simulator`

### 4. Comparison Runner (`comparison_runner.py`)

Orchestrates the comparison:
- Runs each circuit through both pipelines
- Collects results from both
- Handles errors gracefully
- Saves raw comparison results

### 5. Comparison Analyzer (`comparison_analyzer.py`)

Analyzes and compares results:
- Compares state vectors (when available)
- Compares measurement probabilities
- Identifies discrepancies
- Generates JSON and HTML reports

## Output Reports

### JSON Report (`comparison_report.json`)

Contains:
- Summary statistics
- Detailed comparisons for each circuit
- List of discrepancies
- Success rates and agreement rates

### HTML Report (`comparison_report.html`)

Human-readable report with:
- Summary statistics
- Visual indicators (success/failure)
- Discrepancy details
- Detailed comparison table

## Comparison Metrics

1. **Functional Correctness**
   - State vector comparison (for small circuits)
   - Measurement probability comparison
   - Circuit properties matching

2. **Coverage**
   - Circuits that work in both pipelines
   - Circuits that only work in one pipeline
   - Error types and frequencies

3. **Performance**
   - Execution time for each pipeline
   - Resource usage

## Example Output

```
Summary:
  Total Circuits Tested: 15
  Both Passed: 8
  Both Failed: 2
  Qiskit Only Passed: 3
  XMLProgrammer Only Passed: 2
  Discrepancies: 5

Statistics:
  Qiskit Success Rate: 73.33%
  XMLProgrammer Success Rate: 66.67%
  Agreement Rate: 53.33%
```

## Notes

- **State Vector Comparison**: Currently limited by format differences between Qiskit and XMLProgrammer state representations
- **Parameterized Circuits**: Some circuits require parameter binding before testing
- **Error Handling**: Failures in one pipeline don't prevent testing in the other
- **Subset Selection**: Only a subset of circuits is tested to keep execution time manageable

## Future Improvements

- Enhanced state vector comparison with format conversion
- More sophisticated measurement probability comparison
- Performance benchmarking
- Support for more circuit types
- Integration with existing benchmark results











