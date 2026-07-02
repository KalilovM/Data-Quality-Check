from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from dq_impact_monitor.config import PipelineConfig
from dq_impact_monitor.pipeline import run_pipeline


class MonitorRequest(BaseModel):
    days: int = Field(default=90, ge=7, le=365)
    stores: int = Field(default=12, ge=1, le=250)
    anomaly_fraction: float = Field(default=0.08, gt=0, lt=0.5)
    isolation_contamination: float = Field(default=0.08, gt=0, lt=0.5)
    output_dir: str = "artifacts"
    write_database: bool = False


app = FastAPI(
    title="Data Quality Impact Monitor",
    description="Validates daily KPI data and detects business-impacting anomalies.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run-monitor")
def run_monitor(request: MonitorRequest) -> dict[str, object]:
    config = PipelineConfig(
        days=request.days,
        stores=request.stores,
        anomaly_fraction=request.anomaly_fraction,
        isolation_contamination=request.isolation_contamination,
        output_dir=Path(request.output_dir),
        database_url=os.getenv("DATABASE_URL"),
        write_database=request.write_database,
    )
    return run_pipeline(config).to_dict()
