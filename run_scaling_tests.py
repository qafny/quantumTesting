"""Run one generated circuit per subprocess with a timeout and saved progress."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def source_fingerprint(project):
    digest = hashlib.sha256()
    digest.update(sys.version.encode())
    for distribution in ("qiskit", "numpy", "scipy"):
        try:
            digest.update(f"{distribution}={importlib.metadata.version(distribution)}".encode())
        except importlib.metadata.PackageNotFoundError:
            digest.update(f"{distribution}=missing".encode())
    paths = [project / "qet.py", project / "globals.py"]
    for name in ("evaluators", "comparators", "helpers", "parser", "qetast",
                 "writers", "readers", "testers", "generators"):
        paths.extend(sorted((project / name).rglob("*.py")))
    for path in paths:
        if path.is_file():
            digest.update(str(path.relative_to(project)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def summarize(case_dir):
    counts = {key: 0 for key in ("MATCH", "MISMATCH", "ERROR", "REFERENCE_ERROR")}
    files = list((case_dir / "outputs").rglob("results.csv"))
    for path in files:
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                status = row.get("status", "")
                if status not in counts:
                    raise ValueError(f"Unexpected results schema/status in {path}: {status!r}")
                counts[status] += 1
    if not files or not sum(counts.values()):
        raise ValueError("No result rows found; install the updated comparator and run_qet()")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", default="benchmarks/scaling")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--run-dir", help="Reuse this directory with --resume")
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="Seconds per circuit, covering all passes and inputs")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    project = Path(args.project_root).resolve()
    benchmarks = Path(args.benchmark_root).resolve()
    if not (project / "qet.py").is_file():
        parser.error("qet.py not found under --project-root")
    configs = sorted(benchmarks.rglob(".config.json"))
    if not configs:
        parser.error("No .config.json files found under --benchmark-root")
    if args.resume and not args.run_dir:
        parser.error("--resume requires --run-dir")

    default_run = project / "scaling_results" / datetime.now(
        timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run_dir = Path(args.run_dir).resolve() if args.run_dir else default_run
    if run_dir.exists() and any(run_dir.iterdir()) and not args.resume:
        parser.error("Use an empty --run-dir or specify --resume")
    run_dir.mkdir(parents=True, exist_ok=True)
    code_hash = source_fingerprint(project)
    summary_rows = []

    for config_path in configs:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("type") != "custom":
            parser.error(f"Only generated custom benchmarks are supported: {config_path}")
        for circuit_id, info in config["circuits"].items():
            source = config_path.parent / info["circuit_file"]
            input_file = config_path.parent / info["inputs"]["inputs_file"]
            single_config = {"type": "custom", "circuits": {circuit_id: {
                **info, "circuit_file": source.name,
                "inputs": {"type": "json", "inputs_file": input_file.name},
            }}}
            fingerprint = hashlib.sha256(
                source.read_bytes() + input_file.read_bytes()
                + json.dumps(single_config, sort_keys=True).encode()
                + code_hash.encode()
            ).hexdigest()
            label = str(config_path.parent.relative_to(benchmarks)) + "/" + circuit_id
            case_key = hashlib.sha256(label.encode()).hexdigest()[:16]
            case_dir = run_dir / case_key
            case_dir.mkdir(exist_ok=True)
            status_file = case_dir / "status.json"
            previous = json.loads(status_file.read_text()) if status_file.exists() else {}
            if args.resume and previous.get("fingerprint") == fingerprint and previous.get("status") in ("MATCH", "MISMATCH"):
                print(f"SKIP {label}: completed", flush=True)
                summary_rows.append(previous)
                continue
            # Clear outputs from an interrupted or invalidated attempt.
            shutil.rmtree(case_dir / "outputs", ignore_errors=True)
            case_bench = case_dir / "benchmark"
            shutil.rmtree(case_bench, ignore_errors=True)
            case_bench.mkdir()
            shutil.copyfile(source, case_bench / source.name)
            shutil.copyfile(input_file, case_bench / input_file.name)
            write_json(case_bench / ".config.json", single_config)
            generation = info.get("generation", {})
            record = {
                "case": label, "case_dir": str(case_dir), "fingerprint": fingerprint,
                "family": generation.get("family", ""),
                "num_qubits": generation.get("num_qubits", ""),
                "num_gates": generation.get("num_gates", ""),
                "inputs_count": generation.get("inputs_count", ""),
                "status": "RUNNING", "elapsed_s": "", "returncode": "", "error": "",
                "MATCH": 0, "MISMATCH": 0, "ERROR": 0, "REFERENCE_ERROR": 0,
            }
            write_json(status_file, record)
            print(f"RUN  {label}", flush=True)
            started = time.perf_counter()
            command = [sys.executable, "-u", str(project / "qet.py"),
                       "--bench_path", str(case_bench), "--out", str(case_dir / "outputs"),
                       "--log", "30"]
            with (case_dir / "run.log").open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, cwd=project, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.wait()
                    record.update(status="TIMEOUT", error=f"Exceeded {args.timeout} seconds")
                except KeyboardInterrupt:
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.wait()
                    record.update(status="INTERRUPTED", elapsed_s=time.perf_counter()-started)
                    write_json(status_file, record)
                    raise
            record.update(elapsed_s=time.perf_counter()-started, returncode=process.returncode)
            if record["status"] != "TIMEOUT":
                try:
                    record.update(summarize(case_dir))
                    if process.returncode != 0 or record["ERROR"] or record["REFERENCE_ERROR"]:
                        record["status"] = "ERROR"
                    elif record["MISMATCH"]:
                        record["status"] = "MISMATCH"
                    else:
                        record["status"] = "MATCH"
                except Exception as exc:
                    record.update(status="ERROR", error=str(exc))
            write_json(status_file, record)
            summary_rows.append(record)
            with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(record))
                writer.writeheader()
                writer.writerows(summary_rows)
            print(f"{record['status']} {label}: {record['elapsed_s']:.2f}s", flush=True)
    # Also refresh the summary when every case was resumed.
    if summary_rows:
        with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(summary_rows[0]))
            writer.writeheader()
            writer.writerows(summary_rows)
    print(f"Results: {run_dir}")


if __name__ == "__main__":
    main()
