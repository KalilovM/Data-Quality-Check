from __future__ import annotations

from dq_impact_monitor.config import PipelineConfig
from dq_impact_monitor.pipeline import run_pipeline


def test_run_pipeline_creates_metrics_and_outputs(tmp_path) -> None:
    config = PipelineConfig(
        days=21,
        stores=3,
        seed=7,
        anomaly_fraction=0.08,
        isolation_contamination=0.08,
        output_dir=tmp_path,
    )

    result = run_pipeline(config)

    assert result.records_processed == 21 * 3 * 5
    assert result.anomalies_detected > 0
    assert "combined" in result.method_metrics
    assert "precision" in result.method_metrics["combined"]
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "anomalies.csv").exists()
