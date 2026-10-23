"""
MorphQ-style comparator to check optimisation steps
"""

import logging
from time import perf_counter
from typing import Any, Dict, List, Optional
from qiskit import QuantumCircuit, QiskitError, transpile
from qiskit_aer import AerSimulator
from comparators.base import BaseComparator
from helpers.pass_timing import instrument_pass_classes
from scipy.stats import ks_2samp


def _counts_to_samples(counts: Dict[str, int]) -> List[str]:
    samples: List[str] = []
    for bitstring, freq in counts.items():
        samples.extend([bitstring] * int(freq))
    return samples


class _MorphQRunner:
    _BACKEND_MAX_QUBITS = 512 # Raised from default Aer simulator value so we can observe behaviour

    def __init__(self, shots: int = 4096):
        self.shots = shots
        self.backend = AerSimulator(method="statevector")
        try:
            self.backend._configuration.n_qubits = self._BACKEND_MAX_QUBITS
        except Exception:
            logging.warning("Could not raise Aer backend n_qubits")
        self._base_cache: Dict[int, tuple] = {}

    def _prepare_base(self, circuit: QuantumCircuit) -> QuantumCircuit:
        key = id(circuit)
        cached = self._base_cache.get(key)
        if cached is not None and cached[0] is circuit:
            return cached[1].copy()

        base = circuit.remove_final_measurements(inplace=False)

        try:
            base = transpile(base, optimization_level=0, basis_gates=["u", "cx"], coupling_map=None, )
        except Exception as exc_first:
            for _ in range(20):
                try:
                    new_base = base.decompose()
                except Exception:
                    break
                if (
                    new_base.size() == base.size()
                    and new_base.depth() == base.depth()
                ):
                    break
                base = new_base
            try:
                base = transpile(base, optimization_level=0, basis_gates=["u", "cx"], coupling_map=None,)
            except Exception as exc_second:
                raise RuntimeError(
                    "cannot prepare circuit for Aer: "
                    f"transpile={type(exc_first).__name__}({exc_first}); "
                    f"after-decompose={type(exc_second).__name__}"
                    f"({exc_second})"
                ) from exc_second

        base = base.remove_final_measurements(inplace=False)
        self._base_cache[key] = (circuit, base)
        return base.copy()

    def _prepare_with_input(
        self, circuit: QuantumCircuit, ins: Dict[str, bool]
    ) -> QuantumCircuit:
        base = self._prepare_base(circuit)
        qc = QuantumCircuit(base.num_qubits)
        for idx, bit in ins.items():
            if bit:
                qc.x(int(idx))
        qc = qc.compose(base)
        qc.measure_all(inplace=True)
        return qc

    def run_counts(self, measured: QuantumCircuit) -> Dict[str, int]:
        try:
            return (
                self.backend.run(measured, shots=self.shots)
                .result()
                .get_counts(0)
            )
        except QiskitError as exc:
            msg = str(exc)
            if "insufficient memory" in msg.lower():
                raise MemoryError(msg) from exc
            raise

    def ks_divergence(
        self, source_counts: Dict[str, int], follow_counts: Dict[str, int]
    ):
        if ks_2samp is None:
            raise RuntimeError("scipy required for MorphQ KS detector")
        a = _counts_to_samples(source_counts)
        b = _counts_to_samples(follow_counts)
        statistic, p_value = ks_2samp(a, b)
        return float(statistic), float(p_value)

    @staticmethod
    def decide(statistic: float, p_value: float, alpha: float = 0.05) -> str:
        return "DIVERGED" if p_value < alpha else "MATCH"


class MorphQOptimisationPassComparator(BaseComparator):
    def __init__(
        self,
        circuit: QuantumCircuit,
        evaluator_classes: List[type],
        inputs: List[Dict[str, bool]],
        shots: int = 4096,
        alpha: float = 0.05,
    ):
        if not inputs:
            raise ValueError("At least one input required")
        if not evaluator_classes:
            raise ValueError("At least one evaluator class required")
        super().__init__(evaluators=[], inputs=inputs)
        self._circuit = circuit.copy()
        self._classes = list(evaluator_classes)
        self._shots = int(shots)
        self._alpha = float(alpha)
        self._runner = _MorphQRunner(shots=self._shots)
        instrument_pass_classes(self._classes)

    @staticmethod
    def get_identifier() -> str:
        return "morphq"


    def compare(self) -> List[Dict[Any, Any]]:
        self._evaluators.clear()
        inputs = self.get_inputs()
        n_qubits = self._circuit.num_qubits

        ref_start = perf_counter()
        try:
            ref_circuit = self._runner._prepare_with_input(
                self._circuit, inputs[0]
            )
            self._runner.run_counts(ref_circuit)
            reference_preparation_s = perf_counter() - ref_start
            reference_error = ""
        except MemoryError as exc:
            reference_preparation_s = perf_counter() - ref_start
            reference_error = (
                f"MemoryError while preparing reference statevector "
                f"({n_qubits} qubits): {exc}"
            )
            logging.error(
                "MorphQ reference OOM on circuit of %d qubits: %s",
                n_qubits, reference_error,
            )
        except Exception as exc:
            reference_preparation_s = perf_counter() - ref_start
            reference_error = f"{type(exc).__name__}: {exc}"
            logging.error(
                "MorphQ reference run failed on circuit of %d qubits: %s",
                n_qubits, reference_error, exc_info=True,
            )

        rows: List[Dict[Any, Any]] = []
        for cls in self._classes:
            identifier = cls.get_identifier()

            evaluator, initialisation_error = None, ""
            start = perf_counter()
            try:
                evaluator = cls(qc=self._circuit.copy())
                self._evaluators.append(evaluator)
            except Exception as exc:
                logging.exception("MorphQ pass init failed: %s", identifier)
                initialisation_error = f"{type(exc).__name__}: {exc}"
            initialisation_s = perf_counter() - start

            transform_s, gates_after, changed = "", "", ""
            if evaluator is not None:
                transform_s = getattr(evaluator, "transform_time_s", "")
                transformed = evaluator.get_transformed_circuit()
                changed = transformed != self._circuit
                gates_after = len(transformed.data)

            for index, ins in enumerate(inputs):
                row: Dict[Any, Any] = {
                    "input_index": index,
                    "evaluator": identifier,
                    "num_qubits": n_qubits,
                    "original_gate_count": len(self._circuit.data),
                    "transformed_gate_count": gates_after,
                    "circuit_changed": changed,
                    "reference_preparation_s": reference_preparation_s,
                    "evaluator_initialisation_s": initialisation_s,
                    "transform_s": transform_s,
                    "morphq_shots": self._shots,
                    "morphq_alpha": self._alpha,
                    "statistic": "",
                    "p_value": "",
                    "simulation_s": "",
                    "comparison_s": "",
                    "total_s": "",
                }

                if reference_error:
                    row.update(status="REFERENCE_ERROR", error=reference_error)
                    rows.append(row)
                    continue
                if initialisation_error:
                    row.update(status="ERROR", error=initialisation_error)
                    rows.append(row)
                    continue

                source_measured = self._runner._prepare_with_input(
                    self._circuit, ins
                )
                follow_measured = self._runner._prepare_with_input(
                    evaluator.get_transformed_circuit(), ins
                )

                sim_start = perf_counter()
                try:
                    source_counts = self._runner.run_counts(source_measured)
                    follow_counts = self._runner.run_counts(follow_measured)
                    simulation_s = perf_counter() - sim_start
                except MemoryError as exc:
                    simulation_s = perf_counter() - sim_start
                    row.update(
                        status="ERROR",
                        error=(
                            f"MemoryError while simulating "
                            f"({n_qubits} qubits): {exc}"
                        ),
                        simulation_s=simulation_s,
                    )
                    rows.append(row)
                    continue
                except Exception as exc:
                    simulation_s = perf_counter() - sim_start
                    row.update(
                        status="ERROR",
                        error=f"{type(exc).__name__}: {exc}",
                        simulation_s=simulation_s,
                    )
                    rows.append(row)
                    continue

                cmp_start = perf_counter()
                try:
                    statistic, p_value = self._runner.ks_divergence(
                        source_counts, follow_counts
                    )
                    status = self._runner.decide(
                        statistic, p_value, alpha=self._alpha
                    )
                except Exception as exc:
                    row.update(
                        status="ERROR",
                        error=f"KS failed: {type(exc).__name__}: {exc}",
                        simulation_s=simulation_s,
                    )
                    rows.append(row)
                    continue
                comparison_s = perf_counter() - cmp_start

                total_s = None
                if isinstance(transform_s, (int, float)):
                    total_s = (
                        initialisation_s + transform_s
                        + simulation_s + comparison_s
                    )
                else:
                    total_s = initialisation_s + simulation_s + comparison_s

                row.update(
                    statistic=statistic,
                    p_value=p_value,
                    simulation_s=simulation_s,
                    comparison_s=comparison_s,
                    total_s=total_s,
                    status=status,
                    passed=(status == "MATCH"),
                )
                rows.append(row)

        return rows