import logging
from typing import List, Dict, Any, Tuple, Optional
import os
import time

from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
import helpers.qubits as helper_qubits
from testers.base import BaseTester
import math
import numpy as np

from testers.circuit_properties import get_properties_for_circuit
from testers.circuit_properties.base import PropertyResult
from writers.run_context import RunContext


def compute_marginal_probabilities(state: List[Tuple[complex, Dict[str, bool]]], qubit_idx: int) -> float:
    prob = 0.0
    for amp, sd in state:
        if sd.get(str(qubit_idx), False):
            prob += abs(amp) ** 2
    return prob


def compute_parity(state: List[Tuple[complex, Dict[str, bool]]]) -> float:
    even = 0.0
    odd = 0.0
    for amp, sd in state:
        parity = sum(1 for bit in sd.values() if bit) % 2
        if parity == 0:
            even += abs(amp) ** 2
        else:
            odd += abs(amp) ** 2
    return even - odd


def is_unitary_matrix(U: np.ndarray, tol: float = 1e-6) -> bool:
    n = U.shape[0]
    eye = np.eye(n, dtype=complex)
    UHU = U.conj().T @ U
    return np.allclose(UHU, eye, atol=tol)


def are_unitaries_equal(U1: np.ndarray, U2: np.ndarray, tol: float = 1e-6) -> bool:
    for i in range(U1.shape[0]):
        for j in range(U1.shape[1]):
            if abs(U1[i, j]) > tol and abs(U2[i, j]) > tol:
                phase = U1[i, j] / U2[i, j]
                phase = phase / abs(phase)
                return bool(np.allclose(U1, phase * U2, atol=tol))
    return bool(np.allclose(U1, U2, atol=tol))


def normalise_state(state: List[Tuple[complex, Dict[str, bool]]]) -> bool:
    total = sum(abs(amp) ** 2 for amp, _ in state)
    return math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6)


class _EvalResult:
    __slots__ = ("state", "time", "success", "error", "num_qubits")

    def __init__(self) -> None:
        self.state = None
        self.time: float = 0.0
        self.success: bool = False
        self.error: Optional[str] = None
        self.num_qubits: int = 0


def _safe_evaluate(evaluator: BaseEvaluator, ins: Dict[str, bool]) -> _EvalResult:
    res = _EvalResult()
    start = time.perf_counter()
    try:
        state = evaluator.evaluate(ins)
        res.state = state
        res.success = True
        if state:
            res.num_qubits = len(next(iter(state))[1])
    except MemoryError:
        res.error = "MemoryError"
        logging.warning(
            f"Evaluator {evaluator.get_identifier()} ran out of memory "
            f"on input with {len(ins)} qubits"
        )
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
        logging.warning(
            f"Evaluator {evaluator.get_identifier()} failed: {res.error}"
        )
    finally:
        res.time = time.perf_counter() - start
    return res


def _safe_get_unitary(
    evaluator: BaseEvaluator,
) -> Tuple[Optional[np.ndarray], float, bool, Optional[str]]:
    start = time.perf_counter()
    try:
        U = evaluator.get_unitary()
        return U, time.perf_counter() - start, True, None
    except MemoryError:
        return None, time.perf_counter() - start, False, "MemoryError"
    except Exception as e:
        return None, time.perf_counter() - start, False, f"{type(e).__name__}: {e}"



class QuCheckPropertiesPairwiseComparator(BaseComparator):

    MAX_UNITARY_QUBITS = int(os.environ.get("QET_MAX_UNITARY_QUBITS", "8"))

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]], **kwargs):
        logging.info("Initializing QuCheckPropertiesPairwiseComparator")
        super(QuCheckPropertiesPairwiseComparator, self).__init__(evaluators, inputs)
        logging.info("Finished Initializing QuCheckPropertiesPairwiseComparator")
        super().__init__(evaluators, inputs)
        logging.info(
            f"Initializing QuCheckPropertiesPairwiseComparator "
            f"(max_unitary_qubits={self.MAX_UNITARY_QUBITS})"
        )

    @staticmethod
    def get_identifier() -> str:
        return "qcp"

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using QuCheckPropertiesPairwiseComparator")
        run_start = time.perf_counter()

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()

        ctx = RunContext()
        circuit_id_for_props = ctx.current_circuit_id if ctx.is_ready() else ""
        raw_circuit = evaluators[0].get_circuit() if evaluators else None

        circuit_properties: List = []
        if raw_circuit is not None:
            try:
                circuit_properties = get_properties_for_circuit(
                    raw_circuit, circuit_id_for_props
                )
            except Exception as e:
                logging.warning(f"Circuit property lookup failed: {e}")
        logging.info(
            f"Circuit-specific properties for {circuit_id_for_props!r}: "
            f"{[p.name for p in circuit_properties]}"
        )

        n_qubits = 0
        if evaluators:
            try:
                n_qubits = max(
                    ev.get_parsed_circuit().num_qubits for ev in evaluators
                )
            except Exception:
                n_qubits = 0

        do_unitary = 0 < n_qubits <= self.MAX_UNITARY_QUBITS

        if do_unitary:
            logging.info(
                f"Unitary comparison enabled "
                f"(num_qubits={n_qubits}, cap={self.MAX_UNITARY_QUBITS})"
            )
            unitaries: List[Optional[np.ndarray]] = []
            unitary_meta: List[Dict[str, Any]] = []
            for eval_idx, evaluator in enumerate(evaluators):
                eid = evaluator.get_identifier()
                logging.info(f"Computing unitary for evaluator {eval_idx} ({eid})")
                U, elapsed, success, error = _safe_get_unitary(evaluator)
                unitaries.append(U)
                unitary_meta.append({"time": elapsed, "success": success, "error": error})
                logging.info(
                    f"Unitary for evaluator {eval_idx} ({eid}): "
                    f"success={success}, time={elapsed:.3f}s"
                    + (f", error={error}" if error else "")
                )
        else:
            logging.info(
                f"Skipping unitary comparison: num_qubits={n_qubits} "
                f"exceeds cap={self.MAX_UNITARY_QUBITS} "
                f"(override via QET_MAX_UNITARY_QUBITS env var or subclass)"
            )
            unitaries = [None] * len(evaluators)
            unitary_meta = [{"time": 0.0, "success": False, "error": "skipped"}]
            unitary_meta *= len(evaluators)

        outs: List[Dict[Any, Any]] = []

        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            out: Dict[Any, Any] = {
                "input_index": ins_idx,
                "input_num_qubits": len(ins),
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
            }

            eval_states: List[Optional[List]] = [None] * len(evaluators)
            eval_props: List[Optional[Dict[str, float]]] = [None] * len(evaluators)

            for eval_idx, evaluator in enumerate(evaluators):
                eid = evaluator.get_identifier()
                logging.info(f"Evaluating ({eval_idx}) {eid} on input ({ins_idx})")

                result = _safe_evaluate(evaluator, ins)

                out[f"time_evaluator_{eval_idx}_{eid}"] = result.time
                out[f"success_evaluator_{eval_idx}_{eid}"] = result.success
                out[f"num_qubits_evaluator_{eval_idx}_{eid}"] = result.num_qubits

                if not result.success:
                    out[f"error_evaluator_{eval_idx}_{eid}"] = result.error
                    out[f"state_evaluator_{eval_idx}_{eid}"] = None
                    continue

                state = result.state
                eval_states[eval_idx] = state
                out[f"state_evaluator_{eval_idx}_{eid}"] = (
                    helper_qubits.convert_state_to_amp_qet(state)
                )

                if state:
                    n_q = result.num_qubits
                    props: Dict[str, float] = {
                        "is_normalised": 1.0 if normalise_state(state) else 0.0,
                    }
                    for q in range(n_q):
                        props[f"prob_qubit_{q}"] = compute_marginal_probabilities(state, q)
                    props["parity_expectation"] = compute_parity(state)
                    props["prob_zero"] = sum(
                        abs(a) ** 2 for a, sd in state if not any(sd.values())
                    )
                    props["prob_all_ones"] = sum(
                        abs(a) ** 2 for a, sd in state if all(sd.values())
                    )
                    eval_props[eval_idx] = props

            for eval_idx, evaluator in enumerate(evaluators):
                eid = evaluator.get_identifier()
                if do_unitary:
                    U = unitaries[eval_idx]
                    unitary_ok = U is not None and is_unitary_matrix(U)
                    out[f"is_unitary_evaluator_{eval_idx}_{eid}"] = unitary_ok
                    out[f"is_reversible_evaluator_{eval_idx}_{eid}"] = unitary_ok
                    out[f"time_unitary_evaluator_{eval_idx}_{eid}"] = unitary_meta[eval_idx]["time"]
                else:
                    out[f"is_unitary_evaluator_{eval_idx}_{eid}"] = None
                    out[f"is_reversible_evaluator_{eval_idx}_{eid}"] = None

            if do_unitary:
                all_unitaries_equal = True
                if len(unitaries) > 1:
                    for i in range(len(unitaries)):
                        for j in range(i + 1, len(unitaries)):
                            ei = evaluators[i].get_identifier()
                            ej = evaluators[j].get_identifier()
                            if unitaries[i] is None or unitaries[j] is None:
                                eq = False
                            else:
                                eq = are_unitaries_equal(unitaries[i], unitaries[j])
                            out[
                                f"unitary_comp_[evaluator_{i}_{ei}]"
                                f"_[evaluator_{j}_{ej}]"
                            ] = eq
                            if not eq:
                                all_unitaries_equal = False
                out["all_unitaries_equal"] = all_unitaries_equal
            else:
                out["all_unitaries_equal"] = None

            # Pairwise comparison
            for i in range(len(evaluators)):
                for j in range(i + 1, len(evaluators)):
                    ei = evaluators[i].get_identifier()
                    ej = evaluators[j].get_identifier()
                    key = (
                        f"comp_[evaluator_{i}_{ei}]"
                        f"_[evaluator_{j}_{ej}]"
                    )
                    p_i = eval_props[i]
                    p_j = eval_props[j]
                    if p_i is None or p_j is None:
                        out[key] = False
                        continue
                    equal = True
                    for prop_key in p_i:
                        if prop_key not in p_j:
                            equal = False
                            break
                        if not math.isclose(
                            p_i[prop_key], p_j[prop_key],
                            rel_tol=1e-6, abs_tol=1e-6,
                        ):
                            equal = False
                            break
                    out[key] = equal

            # All comparison
            '''
            TODO: 
                1. Check whether, for all properties, the check passes (is equivalent) across all evaluators.
                2. Add the results to out
            '''
            valid_props = [p for p in eval_props if p is not None]
            if len(evaluators) == 1:
                out["comp_evaluator_all"] = True
            elif len(valid_props) != len(evaluators):
                out["comp_evaluator_all"] = False
            else:
                first = valid_props[0]
                all_equal = True
                for p in valid_props[1:]:
                    for prop_key in first:
                        if prop_key not in p or not math.isclose(
                            first[prop_key], p[prop_key],
                            rel_tol=1e-6, abs_tol=1e-6,
                        ):
                            all_equal = False
                            break
                    if not all_equal:
                        break
                out["comp_evaluator_all"] = all_equal

            for eval_idx, props in enumerate(eval_props):
                if props is not None:
                    eid = evaluators[eval_idx].get_identifier()
                    out[f"properties_evaluator_{eval_idx}_{eid}"] = props

            if len(evaluators) >= 2:
                times = [
                    out.get(
                        f"time_evaluator_{i}_{evaluators[i].get_identifier()}",
                        0.0,
                    )
                    for i in range(len(evaluators))
                ]
                out["time_delta_max_min"] = max(times) - min(times)
                out["time_ratio_max_min"] = (
                    max(times) / min(times) if min(times) > 0 else float("inf")
                )


            for eval_idx, evaluator in enumerate(evaluators):
                if eval_states[eval_idx] is None:
                    continue
                eid = evaluator.get_identifier()
                for prop in circuit_properties:
                    key = f"prop_{prop.name}_evaluator_{eval_idx}_{eid}"
                    try:
                        res = prop.check(
                            raw_circuit, circuit_id_for_props,
                            ins, eval_states[eval_idx], len(ins),
                        )
                    except Exception as e:
                        res = PropertyResult(
                            False,
                            f"exception {type(e).__name__}: {e}",
                        )
                    out[key] = res.passed
                    if not res.passed:
                        out[f"prop_{prop.name}_reason_{eval_idx}_{eid}"] = res.reason

            for prop in circuit_properties:
                vals = []
                for i in range(len(evaluators)):
                    k = f"prop_{prop.name}_evaluator_{i}_{evaluators[i].get_identifier()}"
                    if k in out:
                        vals.append(out[k])
                out[f"prop_{prop.name}_all_pass"] = bool(vals) and all(vals)
                out[f"prop_{prop.name}_all_same"] = len(set(vals)) <= 1

            outs.append(out)

        self._log_circuit_summary(
            evaluators, outs, time.perf_counter() - run_start,
            circuit_properties=circuit_properties,
        )
        self._write_incremental(outs)

        logging.info("Finished Comparing using QuCheckPropertiesPairwiseComparator")

        return outs

    def _log_circuit_summary(self, evaluators, outs, circuit_time, circuit_properties=None):
        logging.info("=" * 72)
        logging.info("QCP per-circuit summary")
        logging.info("=" * 72)
        for eval_idx, evaluator in enumerate(evaluators):
            eid = evaluator.get_identifier()
            times, successes, qsizes = [], [], []
            for o in outs:
                tk = f"time_evaluator_{eval_idx}_{eid}"
                sk = f"success_evaluator_{eval_idx}_{eid}"
                qk = f"num_qubits_evaluator_{eval_idx}_{eid}"
                if tk in o:
                    times.append(o[tk])
                if sk in o:
                    successes.append(o[sk])
                if qk in o and o[qk]:
                    qsizes.append(o[qk])
            n = len(times)
            if n == 0:
                logging.info(f"  {eid}: no results")
                continue
            logging.info(
                f"  {eid}: inputs={n}, "
                f"success={sum(successes)}/{n}, "
                f"avg_time={sum(times) / n:.6f}s, "
                f"total_time={sum(times):.6f}s, "
                f"max_time={max(times):.6f}s, "
                f"max_qubits={max(qsizes) if qsizes else 0}"
            )

        if circuit_properties:
            logging.info("  -- circuit-specific properties --")
            for prop in circuit_properties:
                parts = []
                for eval_idx, evaluator in enumerate(evaluators):
                    eid = evaluator.get_identifier()
                    k = f"prop_{prop.name}_evaluator_{eval_idx}_{eid}"
                    passed = sum(1 for o in outs if o.get(k) is True)
                    total = sum(1 for o in outs if k in o)
                    if total:
                        parts.append(f"{eid}: {passed}/{total}")
                logging.info(f"    {prop.name}: " + " | ".join(parts))

        logging.info(f"  circuit_total_time={circuit_time:.3f}s")
        logging.info("=" * 72)

    def _write_incremental(self, outs: List[Dict[Any, Any]]) -> None:
        try:
            from writers.run_context import RunContext
            from writers.csv import ComparatorOutputCSVWriter
            from writers import qcp_summary as summary_io
        except Exception as e:
            logging.warning(f"Incremental write disabled: {e}")
            return

        ctx = RunContext()
        if not ctx.is_ready():
            logging.debug("RunContext not ready; skipping incremental write")
            return

        circuit_id = ctx.current_circuit_id
        run_path = ctx.run_path()
        base_path = ctx.base_path()
        benchmark_id = ctx.benchmark_id()
        run_id = ctx.run_id()

        try:
            csv_writer = ComparatorOutputCSVWriter(base_path, benchmark_id, run_id)
            csv_path = csv_writer.write_circuit(circuit_id, outs)

            summary = summary_io.compute_circuit_summary(
                circuit_id=circuit_id,
                rows=outs,
                benchmark_id=benchmark_id,
                run_id=run_id,
            )
            summary_path = summary_io.write_circuit_summary(
                run_path, circuit_id, summary
            )

            ctx.record_results(circuit_id, outs)
            run_summary = summary_io.compute_run_summary(
                accumulated=ctx.accumulated,
                benchmark_id=benchmark_id,
                run_id=run_id,
                elapsed_seconds=0.0,
            )
            run_summary_path = summary_io.write_run_summary(run_path, run_summary)

            logging.info(
                f"Incremental write: {csv_path}, {summary_path}, {run_summary_path}"
            )
        except Exception as e:
            logging.warning(f"Incremental write failed: {type(e).__name__}: {e}")

class QuCheckExpectedPropertiesComparator(BaseComparator):

    def __init__(self, evaluators: List[BaseEvaluator], inputs: List[Dict[str, bool]], testers: Optional[List[BaseTester]] = None, **kwargs):
        super().__init__(evaluators, inputs)
        self.testers: List[BaseTester] = testers or []
        logging.info("Initializing QuCheckExpectedPropertiesComparator")

    @staticmethod
    def get_identifier() -> str:
        return "qcio"

    def compare(self) -> List[Dict[Any, Any]]:
        logging.info("Comparing using QuCheckExpectedPropertiesComparator")

        evaluators = self.get_evaluators()
        inputs = self.get_inputs()
        testers = self.testers

        outs: List[Dict[Any, Any]] = []
        for ins_idx, ins in enumerate(inputs):
            system_state_ins: List[Tuple[complex, Dict[str, bool]]] = helper_qubits.get_system_state_from_qubits(ins)
            out: Dict[Any, Any] = {
                "input_index": ins_idx,
                "input_num_qubits": len(ins),
                "input": helper_qubits.convert_state_to_amp_qet(system_state_ins),
            }

            for eval_idx, evaluator in enumerate(evaluators):
                eid = evaluator.get_identifier()
                logging.info(f"Evaluating ({eval_idx}) {eid} on input ({ins_idx})")
                result = _safe_evaluate(evaluator, ins)

                out[f"time_evaluator_{eval_idx}_{eid}"] = result.time
                out[f"success_evaluator_{eval_idx}_{eid}"] = result.success
                out[f"num_qubits_evaluator_{eval_idx}_{eid}"] = result.num_qubits

                if not result.success:
                    out[f"error_evaluator_{eval_idx}_{eid}"] = result.error
                    out[f"state_evaluator_{eval_idx}_{eid}"] = None
                    continue

                state = result.state
                out[f"state_evaluator_{eval_idx}_{eid}"] = (
                    helper_qubits.convert_state_to_amp_qet(state)
                )

                for tester_idx, tester in enumerate(testers):
                    logging.info(f"Running tester ({tester_idx}) {tester.get_identifier()}")
                    try:
                        tester_result = tester.test(
                            evaluator=evaluator, input=ins, state=state
                        )
                    except Exception as e:
                        tester_result = False
                        out[f"tester_error_{eval_idx}_{tester_idx}"] = (
                            f"{type(e).__name__}: {e}"
                        )
                    out[
                        f"result_eval_{eval_idx}_{eid}"
                        f"_tester_{tester_idx}_{tester.get_identifier()}"
                    ] = tester_result

            outs.append(out)

        logging.info("Finished Comparing using QuCheckExpectedPropertiesComparator")

        return outs
