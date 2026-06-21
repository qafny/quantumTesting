import importlib
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from qiskit import QuantumCircuit
from generators.inputs import BaseInputGenerator


class BaseQiskitBenchmark(ABC):

    def __init__(self, benchmark_folder: str):
        self._benchmark_folder = benchmark_folder

    def get_benchmark_folder(self) -> str:
        return self._benchmark_folder

    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def get_qiskit_circuits(self) -> Dict[str, QuantumCircuit]:
        pass

    @abstractmethod
    def get_inputs(self) -> Dict[str, List[Dict[str, bool]]]:
        pass


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
                    case "custom":
                        inputs_file = inputs_info.get("inputs_file", None)
                        inputs_name = inputs_info.get("inputs_name", None)

                        namespace = {}
                        with open(inputs_file, "r") as file:
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
