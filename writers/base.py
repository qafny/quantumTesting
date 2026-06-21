from abc import ABC, abstractmethod
from pathlib import Path


class BaseWriter(ABC):

    def __init__(self, base_path: str, benchmark_path: str, run_id: str):
        self._base_path: str = base_path
        self._benchmark_id: str = Path(benchmark_path).name
        self._run_path = f"{self._base_path}/{run_id}"

        Path(self._run_path).mkdir(parents=True, exist_ok=True)

    def get_base_path(self):
        return self._base_path

    def get_benchmark_id(self):
        return self._benchmark_id

    def get_run_path(self):
        return self._run_path

    @abstractmethod
    def write(self):
        pass
