from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    days: int = 90
    stores: int = 12
    seed: int = 42
    anomaly_fraction: float = 0.08
    isolation_contamination: float = 0.08
    output_dir: Path = Path("artifacts")
    database_url: str | None = None
    write_database: bool = False

    def __post_init__(self) -> None:
        if self.days < 7:
            raise ValueError("days must be at least 7 so rolling KPI features are meaningful")
        if self.stores < 1:
            raise ValueError("stores must be greater than zero")
        if not 0 < self.anomaly_fraction < 0.5:
            raise ValueError("anomaly_fraction must be between 0 and 0.5")
        if not 0 < self.isolation_contamination < 0.5:
            raise ValueError("isolation_contamination must be between 0 and 0.5")
