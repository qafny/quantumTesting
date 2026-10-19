"""Compare each pass against the original circuit; record timings and errors."""

import logging
from time import perf_counter

from comparators.base import BaseComparator
from evaluators.qet import QETEvaluator
from helpers.pass_timing import instrument_pass_classes
import helpers.qubits as helper_qubits


class OptimizationPassComparator(BaseComparator):
    def __init__(self, circuit, evaluator_classes, inputs):
        if not inputs:
            raise ValueError("At least one input is required")
        if not evaluator_classes:
            raise ValueError("At least one evaluator class is required")
        super().__init__(evaluators=[], inputs=inputs)
        self._circuit = circuit.copy()
        self._classes = list(evaluator_classes)
        instrument_pass_classes(self._classes)

    @staticmethod
    def get_identifier():
        return "optpass"

    def compare(self):
        self._evaluators.clear()
        inputs = self.get_inputs()
        reference_start = perf_counter()
        reference = None
        reference_error = ""
        try:
            reference = QETEvaluator(qc=self._circuit.copy(), optimization_level=0)
        except Exception as exc:
            logging.exception("Reference preparation failed")
            reference_error = f"{type(exc).__name__}: {exc}"
        reference_preparation = perf_counter() - reference_start

        expected = []
        for ins in inputs:
            start = perf_counter()
            state, error = None, reference_error
            if reference is not None:
                try:
                    state = reference.evaluate(ins.copy())
                except Exception as exc:
                    logging.exception("Reference simulation failed")
                    error = f"{type(exc).__name__}: {exc}"
            expected.append((state, perf_counter() - start, error))

        rows = []
        for cls in self._classes:
            identifier = cls.get_identifier()
            evaluator, initialization_error = None, ""
            start = perf_counter()
            if reference is not None:
                try:
                    evaluator = cls(qc=self._circuit.copy())
                    self._evaluators.append(evaluator)
                except Exception as exc:
                    logging.exception("Pass preparation failed: %s", identifier)
                    initialization_error = f"{type(exc).__name__}: {exc}"
            initialization_s = perf_counter() - start
            transform_s, preparation_s, changed, gates_after = "", "", "", ""
            if evaluator is not None:
                transform_s = evaluator.transform_time_s
                preparation_s = max(0.0, initialization_s - transform_s)
                transformed = evaluator.get_transformed_circuit()
                changed = transformed != self._circuit
                gates_after = len(transformed.data)

            for index, ins in enumerate(inputs):
                state, reference_simulation_s, error = expected[index]
                row = {
                    "input_index": index, "evaluator": identifier,
                    "input": helper_qubits.convert_state_to_amp_qet(
                        helper_qubits.get_system_state_from_qubits(ins)),
                    "expected": helper_qubits.convert_state_to_amp_qet(state)
                        if state is not None else "",
                    "actual": "", "status": "", "passed": "", "error": "",
                    "num_qubits": self._circuit.num_qubits,
                    "original_gate_count": len(self._circuit.data),
                    "transformed_gate_count": gates_after, "circuit_changed": changed,
                    "reference_preparation_s": reference_preparation,
                    "reference_simulation_s": reference_simulation_s,
                    "evaluator_initialization_s": initialization_s,
                    "transform_s": transform_s, "qet_preparation_s": preparation_s,
                    "simulation_s": "", "comparison_s": "",
                }
                if error:
                    row.update(status="REFERENCE_ERROR", error=error)
                elif initialization_error:
                    row.update(status="ERROR", error=initialization_error)
                else:
                    start = perf_counter()
                    try:
                        actual = evaluator.evaluate(ins.copy())
                        row["simulation_s"] = perf_counter() - start
                        row["actual"] = helper_qubits.convert_state_to_amp_qet(actual)
                    except Exception as exc:
                        row["simulation_s"] = perf_counter() - start
                        row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")
                        logging.exception("Simulation failed: %s input %d", identifier, index)
                    else:
                        start = perf_counter()
                        try:
                            passed = helper_qubits.compare_two_states(actual, state)
                            row.update(status="MATCH" if passed else "MISMATCH", passed=passed)
                        except Exception as exc:
                            row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")
                            logging.exception("Comparison failed: %s", identifier)
                        row["comparison_s"] = perf_counter() - start
                rows.append(row)
        return rows