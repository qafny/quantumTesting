from typing import Dict, List
from writers.base import BaseWriter
from pathlib import Path
import csv


class ComparatorOutputCSVWriter(BaseWriter):

    def __init__(self, base_path: str, benchmark_path: str, run_id: str):
        super(ComparatorOutputCSVWriter, self).__init__(base_path, benchmark_path, run_id)

    @staticmethod
    def _union_fieldnames(rows: List[Dict]) -> List[str]:
        fieldnames: List[str] = []
        seen = set()
        for row in rows:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    fieldnames.append(k)
        return fieldnames

    @classmethod
    def _write_rows_to(cls, csv_path: Path, rows: List[Dict]) -> None:
        if not rows:
            Path(csv_path).touch()
            return
        fieldnames = cls._union_fieldnames(rows)
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                extrasaction="ignore",
                restval="",
            )
            writer.writeheader()
            writer.writerows(rows)

    def write_circuit(self, circuit_id: str, rows: List[Dict]) -> str:
        circuit_path = Path(f"{self.get_run_path()}/{circuit_id}")
        circuit_path.mkdir(parents=True, exist_ok=True)
        csv_path = circuit_path / "results.csv"
        self._write_rows_to(csv_path, rows)
        return str(csv_path)

    def write(self, comparator_outputs: Dict[str, List[Dict]]):
        for circuit_id, rows in comparator_outputs.items():
            self.write_circuit(circuit_id, rows)