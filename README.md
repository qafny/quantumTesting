# QET: Quantum Effective Testing

## Adding a Benchmark Program

QET performs differential testing on different target platforms for quantum programs. In this regard, the quantum programs provided as input for QET must be defined as benchmarks. Refer to the `benchmarks/` directory for the current collection of benchmark programs.

The following instructions explain how to add a new benchmark program to QET.

### Step 1: Create a Benchmark Directory

Create a new directory with an appropriate name inside the `benchmarks/` directory. While benchmarks can be stored elsewhere, it is strongly recommended that benchmark programs intended to be part of the standard QET benchmark suite be organized under the `benchmarks/` directory.

### Step 2: Create the Configuration File

Create a file named `.config.json` inside the benchmark directory. The filename must match exactly, including the leading dot (`.`).

### Step 3: Define the Benchmark

Define the benchmark in the `.config.json` file according to the type of benchmark being added.

#### Library-Based Benchmarks

If the benchmark is based on a Qiskit library circuit or a community circuit, use the following configuration template with `"type": "library"`:

```json
{
  "type": "library",
  "description": "benchmark_description",
  "circuits": {
    "circuit_1": {
      "class_name": "circuit_class_name",
      "module": "circuit_package_name",
      "kwargs": {
        "kwarg_1": "kwarg_value_1",
         ...
      },
      "inputs": {
        "type": "input_generator_type",
        "class_name": "input_generator_class_name",
        "module": "input_generator_package_name",
        "kwargs": {
          "kwarg_1": "kwarg_value_1",
           ...
        }
      }
    },
    "circuit_2": ...
  }
}
```

#### Custom Qiskit Benchmarks

If the benchmark is implemented as a custom Qiskit program, use the following configuration template with `"type": "custom"`:

```json
{
  "type": "custom",
  "description": "benchmark_description",
  "circuits": {
    "circuit_1": {
      "circuit_file": "circuit_file_name.py",
      "circuit_name": "circuit_variable_identifier",
      "inputs": {
        "type": "input_generator_type",
        "class_name": "input_generator_class_name",
        "module": "input_generator_package_name",
        "kwargs": {
          "kwarg_1": "kwarg_value_1",
           ...
        }
      }
    },
    "circuit_2": ...
  }
}
```

### Input Generation

In the configurations above, inputs to the programs may be generated using either a built-in input generator or a custom input-generation script.

#### Using a Built-In Input Generator

If you intend to use an input generator provided by QET (see the `generators.input` module), use the following configuration with `"type": "generator"`:

```json
{
  ...
  "inputs": {
    "type": "generator",
    "class_name": "input_generator_class_name",
    "module": "input_generator_package_name",
    "kwargs": {
      "kwarg_1": "kwarg_value_1",
       ...
    }
  },
  ...
}
```

#### Using a JSON File as Input

If you intend to use a JSON file as an input (check below for the file format), use the following configuration with `"type": "json"`:

```json
{
  ...
  "inputs": {
    "type": "json",
    "inputs_file": "input_json_file_name"
  },
  ...
}
```

#### Using a Custom Input Generator

If you intend to implement a custom input-generation strategy, use the following configuration with `"type": "custom"`. The referenced file must be located in the same directory as the `.config.json` file.

```json
{
  ...
  "inputs": {
    "type": "custom",
    "inputs_file": "input_generator_file_name.py",
    "inputs_name": "input_generator_variable_identifier"
  },
  ...
}
```

The JSON file is expected to be in the following format.

```json
[
  {
    "0": true/false,
    "1": true/false,
    ...
    "n": true/false
  },
  ...
]
```

The file should be a list fo dictionaries. Each dictionary represents an instance of input. `n` is the number of input qubits to the circuit. Hence, each dictionary is expected to contain `n` key-value pairs representing initial qubit id-qubit value pairs.

### Expected Output Generation

Some comparators require the expected outputs corresponding to the generated inputs in order to evaluate correctness. In such cases, you must also provide an outputs configuration. The outputs configuration is defined in the same manner as the inputs configuration. In most cases, the configuration structure is identical, with the property name inputs replaced by outputs. For example, the following configuration defines expected outputs using a JSON-based output generator:

```json
  ...
  "outputs": {
    "type": "json",
    "outputs_file": "file_name.json"
  },
  ...
```

Currently, the following comparators require expected outputs if used:
- sio (Simple Output-Expected Output Comparator): Used for comparing the program output against the expected output

## Setup and Run QET

It is highly recommended to use PyCharm to set up the project, as it automates many of the steps described below.

**Recommended Python Version:** Python 3.14

QET may or may not work with earlier Python versions.

### 1. Create a Virtual Environment

It is recommended to create a virtual environment for the project. Refer to the official Python documentation for instructions on creating, activating, and deactivating virtual environments:

https://docs.python.org/3/library/venv.html

### 2. Install Dependencies

After creating and activating the virtual environment, install the required dependencies. For the complete list of dependencies, refer to `requirements.txt`.

Run the following command:

```bash
pip install -r requirements.txt
```

### 3. Run QET

The main entry point for QET is `qet.py`.

To run QET, select or define a benchmark and execute:

```bash
python qet.py --bench_path=benchmarks/arithmetic --comp=spa --out=.outputs --evals qet tsim
```

## Parameter Definitions

- `bench_path`: Path to the benchmark directory. This directory must contain a `.config.json` file.
- `evals`: List of evaluators to use. Include `qet` for `QETSimulator` and `tsim` for QuEra's TSim Sampler. By default, both evaluators are used.
- `comp`: Comparator used for result comparison. For pairwise comparison, use `spa`. For output vs. expected output comparison, use `sio`. The default comparator is `spa` (`Simple Pairwise Comparator`).
- `opt_level`: The optimization level to use for Qiskit Transpilation. Defaults to 0 (no optimization). Supports levels 0, 1, 2.
- `out`: Output directory. The default value is `.output`. Ensure that this directory is excluded from version control.
- `log`: Logging level. The default value is `logging.DEBUG`.

## Important Notes

If you use PyCharm, the virtual environment setup and dependency installation steps are largely automated.

Instead of running QET from the command line, you can create a Run Configuration with:

- The working directory set to the repository root.
- The desired command-line arguments specified in the configuration.

This approach is often more convenient during development and debugging.