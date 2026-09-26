"""
Keeps track of per-circuit results to write as output for property tests
"""

from typing import Optional, Dict, Any, List


class RunContext:
    _instance: Optional["RunContext"] = None

    def __new__(cls) -> "RunContext":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self) -> None:
        self.writer = None
        self.current_circuit_id: Optional[str] = None
        self.accumulated: Dict[str, List[Dict[str, Any]]] = {}

    def reset(self) -> None:
        self._reset()

    def update(self, writer, circuit_id: str) -> None:
        self.writer = writer
        self.current_circuit_id = circuit_id

    def record_results(self, circuit_id: str, rows: List[Dict[str, Any]]) -> None:
        self.accumulated[circuit_id] = rows

    def is_ready(self) -> bool:
        return self.writer is not None and self.current_circuit_id is not None

    def run_path(self) -> Optional[str]:
        return self.writer.get_run_path() if self.writer is not None else None

    def base_path(self) -> Optional[str]:
        return self.writer.get_base_path() if self.writer is not None else None

    def benchmark_id(self) -> Optional[str]:
        return self.writer.get_benchmark_id() if self.writer is not None else None

    def run_id(self) -> Optional[str]:
        p = self.run_path()
        return p.rsplit("/", 1)[-1] if p else None