import importlib
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from qiskit import QuantumCircuit
from generators.inputs import BaseInputGenerator
import helpers.inputs as helper_inputs


class BaseQiskitBenchmark(ABC):

    def __init__(self, benchmark_folder: str):
        self._benchmark_folder = benchmark_folder
        self.config = None

    def get_benchmark_folder(self) -> str:
        return self._benchmark_folder

    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def get_qiskit_circuits(self) -> Dict[str, QuantumCircuit]:
        pass

    def get_inputs_from_info(self, circuit_info: Dict[str, Any]) -> List[Dict[str, bool]]:
        inputs_info = circuit_info.get("inputs", None)
        if inputs_info is not None:
            inputs_type = inputs_info.get("type", None)
            if inputs_type is not None:
                match inputs_type:
                    case "generator":
                        module_path = inputs_info.get("module", None)
                        class_name = inputs_info.get("class_name", None)
                        kwargs = inputs_info.get("kwargs", None)
                        module = importlib.import_module(module_path)
                        generator_class: type[BaseInputGenerator] = getattr(module, class_name)
                        generator = generator_class(**kwargs)

                        return generator.generate()
                    case "specification":
                        ## TODO: Write a generator to generate outputs using a specification
                        return None
                    case "json":
                        inputs_file_name = inputs_info.get("inputs_file", None)
                        inputs_file_path = f"{self.get_benchmark_folder()}/{inputs_file_name}"
                        return helper_inputs.read_json_file(inputs_file_path)
                    case "custom":
                        inputs_file_name = inputs_info.get("inputs_file", None)
                        inputs_name = inputs_info.get("inputs_name", None)

                        namespace = {}
                        inputs_file_path = f"{self.get_benchmark_folder()}/{inputs_file_name}"
                        with open(inputs_file_path, "r") as file:
                            exec(file.read(), namespace)

                        return namespace.get(inputs_name)
                    case _:
                        raise Exception(f"Invalid inputs configuration in config file at {self.get_benchmark_folder()}")
            else:
                raise Exception(f"Inputs type not found in config file at {self.get_benchmark_folder()}")
        else:
            raise Exception(f"Inputs not found in config file at {self.get_benchmark_folder()}")

    def get_inputs(self) -> Dict[str, List[Dict[str, bool]]]:
        circuits_info = self.config.get("circuits", None)
        if circuits_info is not None:
            inputs = {}
            for circuit_id, circuit_info in circuits_info.items():
                input_list: List[Dict[str, bool]] = self.get_inputs_from_info(circuit_info)
                inputs[circuit_id] = input_list

            return inputs
        else:
            raise Exception(f"Circuits not found in config file at {self.get_benchmark_folder()}")

    def get_outputs_from_info(self, circuit_info: Dict[str, Any]) -> List[Dict[str, bool]]:
        outputs = circuit_info.get("outputs", None)
        if outputs is not None:
            outputs_type = outputs.get("type", None)
            if outputs_type is not None:
                match outputs_type:
                    case "specification":
                        ## TODO: Write a generator to generate outputs using a specification
                        return None
                    case "json":
                        outputs_file_name = outputs.get("outputs_file", None)
                        outputs_file_path = f"{self.get_benchmark_folder()}/{outputs_file_name}"
                        return helper_inputs.read_json_file(outputs_file_path)
                    case "custom":
                        outputs_file_name = outputs.get("outputs_file", None)
                        outputs_name = outputs.get("outputs_name", None)

                        namespace = {}
                        outputs_file_path = f"{self.get_benchmark_folder()}/{outputs_file_name}"
                        with open(outputs_file_path, "r") as file:
                            exec(file.read(), namespace)

                        return namespace.get(outputs_name)
                    case _:
                        raise Exception(f"Invalid outputs configuration in config file at {self.get_benchmark_folder()}")
            else:
                raise Exception(f"Outputs type not found in config file at {self.get_benchmark_folder()}")
        else:
            raise Exception(f"Outputs not found in config file at {self.get_benchmark_folder()}")

    def get_outputs(self) -> Dict[str, List[Dict[str, bool]]]:
        circuits_info = self.config.get("circuits", None)
        if circuits_info is not None:
            outputs = {}
            for circuit_id, circuit_info in circuits_info.items():
                try:
                    outputs_list: List[Dict[str, bool]] = self.get_outputs_from_info(circuit_info)
                    outputs[circuit_id] = outputs_list

                except Exception as e:
                    outputs[circuit_id] = None

            return outputs
        else:
            raise Exception(f"Circuits not found in config file at {self.get_benchmark_folder()}")


class LibraryQiskitBenchmark(BaseQiskitBenchmark):

    def __init__(self, benchmark_folder: str):
        super(LibraryQiskitBenchmark, self).__init__(benchmark_folder)
        self._init_benchmark()

    @staticmethod
    def is_library_benchmark(benchmark_folder: str):
        config_file_path = os.path.join(benchmark_folder, ".config.json")
        if not os.path.exists(config_file_path):
            return False

        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)

        return config.get("type", "") == "library"

    def _init_benchmark(self):
        config_file_path = os.path.join(self.get_benchmark_folder(), ".config.json")
        if not os.path.exists(config_file_path):
            raise Exception(f"Config file not found at {config_file_path}")

        with open(config_file_path, "r") as config_file:
            self.config = json.load(config_file)

    def get_type(self) -> str:
        return self.config.get("type", None)

    def get_circuit_from_info(self, circuit_info: Dict[str, Any]) -> QuantumCircuit:
        module_path = circuit_info["module"]
        class_name = circuit_info["class_name"]

        module = importlib.import_module(module_path)
        circuit_class = getattr(module, class_name)

        kwargs = circuit_info["kwargs"]
        circuit = circuit_class(**kwargs)

        return circuit

    def get_qiskit_circuits(self) -> Dict[str, QuantumCircuit]:
        circuits_info = self.config.get("circuits", None)
        if circuits_info is not None:
            circuits = {}
            for circuit_id, circuit_info in circuits_info.items():
                circuit: QuantumCircuit = self.get_circuit_from_info(circuit_info)
                circuits[circuit_id] = circuit

            return circuits
        else:
            raise Exception(f"Circuits not found in config file at {self.get_benchmark_folder()}")


class CustomQiskitBenchmark(BaseQiskitBenchmark):

    def __init__(self, benchmark_folder: str):
        super(CustomQiskitBenchmark, self).__init__(benchmark_folder)
        self._init_benchmark()

    @staticmethod
    def is_custom_benchmark(benchmark_folder: str):
        config_file_path = os.path.join(benchmark_folder, ".config.json")
        if not os.path.exists(config_file_path):
            return False

        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)

        return config.get("type", "") == "custom"

    def _init_benchmark(self):
        config_file_path = os.path.join(self.get_benchmark_folder(), ".config.json")
        if not os.path.exists(config_file_path):
            raise Exception(f"Config file not found at {config_file_path}")

        with open(config_file_path, "r") as config_file:
            self.config = json.load(config_file)

    def get_type(self) -> str:
        return self.config.get("type", None)

    def get_circuit_from_info(self, circuit_info: Dict[str, Any]) -> QuantumCircuit:
        circuit_file = circuit_info.get("circuit_file", None)
        circuit_name = circuit_info.get("circuit_name", None)

        namespace = {}
        circuit_path = f"{self.get_benchmark_folder()}/{circuit_file}"
        with open(circuit_path, "r") as file:
            exec(file.read(), namespace)

        return namespace.get(circuit_name)

    def get_qiskit_circuits(self) -> Dict[str, QuantumCircuit]:
        circuits_info = self.config.get("circuits", None)
        if circuits_info is not None:
            circuits = {}
            for circuit_id, circuit_info in circuits_info.items():
                circuit: QuantumCircuit = self.get_circuit_from_info(circuit_info)
                circuits[circuit_id] = circuit

            return circuits
        else:
            raise Exception(f"Circuits not found in config file at {self.get_benchmark_folder()}")
