from typing import Dict, List
from writers.base import BaseWriter
from pathlib import Path
import csv


class ComparatorOutputCSVWriter(BaseWriter):

    def __init__(self, base_path: str, benchmark_path: str, run_id: str):
        super(ComparatorOutputCSVWriter, self).__init__(base_path, benchmark_path, run_id)

    def write(self, comparator_outputs: Dict[str, List[Dict[str, bool]]]):
        for circuit_id in comparator_outputs.keys():
            circuit_path = f"{self.get_run_path()}/{circuit_id}"
            Path(circuit_path).mkdir(parents=True, exist_ok=True)

            csv_path = f"{circuit_path}/results.csv"
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, comparator_outputs[circuit_id][0].keys())
                writer.writeheader()
                writer.writerows(comparator_outputs[circuit_id])
