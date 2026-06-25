from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from dq_impact_monitor.config import PipelineConfig
from dq_impact_monitor.detection import (
    combine_findings,
    run_isolation_forest,
    run_statistical_rules,
)
from dq_impact_monitor.features import build_features
from dq_impact_monitor.metrics import anomaly_type_recall, classification_metrics
from dq_impact_monitor.severity import classify_severity
from dq_impact_monitor.synthetic_data import generate_sales_data
from dq_impact_monitor.validation import validate_sales_data


@dataclass(frozen=True)
class PipelineRunResult:
    records_processed: int
    anomalies_detected: int
    processing_seconds: float
    severity_counts: dict[str, int]
    method_metrics: dict[str, dict[str, float | int]]
    anomaly_type_recall: dict[str, float]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_pipeline(config: PipelineConfig) -> PipelineRunResult:
    started = time.perf_counter()
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_data = generate_sales_data(config)
    validation_findings = validate_sales_data(raw_data)
    featured_data = build_features(raw_data)
    statistical_findings = run_statistical_rules(featured_data)
    ml_findings = run_isolation_forest(
        featured_data,
        contamination=config.isolation_contamination,
        seed=config.seed,
    )

    combined_findings = combine_findings(validation_findings, statistical_findings, ml_findings)
    severity_findings = classify_severity(combined_findings)
    anomalies = _build_anomaly_output(featured_data, severity_findings)

    true_labels = raw_data["is_injected_anomaly"].astype(bool)
    method_metrics = {
        "validation": _metrics_for_findings(true_labels, validation_findings),
        "statistical_rules": _metrics_for_findings(true_labels, statistical_findings),
        "isolation_forest": _metrics_for_findings(true_labels, ml_findings),
        "combined": _metrics_for_findings(true_labels, severity_findings),
    }
    detected_indexes = set(severity_findings["row_index"].astype(int).tolist())
    type_recall = anomaly_type_recall(raw_data, detected_indexes)
    severity_counts = {
        str(key): int(value)
        for key, value in anomalies["severity"].value_counts().sort_index().to_dict().items()
    }

    outputs = _write_outputs(
        output_dir=output_dir,
        raw_data=raw_data,
        validation_findings=validation_findings,
        statistical_findings=statistical_findings,
        ml_findings=ml_findings,
        anomalies=anomalies,
        metrics={
            "records_processed": int(len(raw_data)),
            "anomalies_detected": int(len(anomalies)),
            "processing_seconds": 0.0,
            "severity_counts": severity_counts,
            "method_metrics": method_metrics,
            "anomaly_type_recall": type_recall,
        },
    )

    processing_seconds = round(time.perf_counter() - started, 4)
    result = PipelineRunResult(
        records_processed=int(len(raw_data)),
        anomalies_detected=int(len(anomalies)),
        processing_seconds=processing_seconds,
        severity_counts=severity_counts,
        method_metrics=method_metrics,
        anomaly_type_recall=type_recall,
        outputs=outputs,
    )

    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    if config.write_database and config.database_url:
        from dq_impact_monitor.storage import write_pipeline_outputs

        write_pipeline_outputs(
            database_url=config.database_url,
            raw_data=raw_data,
            anomalies=anomalies,
            metrics=result.to_dict(),
        )

    return result


def _build_anomaly_output(frame: pd.DataFrame, severity_findings: pd.DataFrame) -> pd.DataFrame:
    if severity_findings.empty:
        return pd.DataFrame()

    anomaly_rows = frame.loc[severity_findings["row_index"].astype(int)].copy()
    anomaly_rows = anomaly_rows.reset_index(names="row_index")
    return anomaly_rows.merge(severity_findings, on="row_index", how="left")


def _metrics_for_findings(y_true: pd.Series, findings: pd.DataFrame) -> dict[str, float | int]:
    predictions = pd.Series(False, index=y_true.index)
    if not findings.empty:
        predictions.loc[findings["row_index"].astype(int)] = True
    return classification_metrics(y_true, predictions)


def _write_outputs(
    output_dir: Path,
    raw_data: pd.DataFrame,
    validation_findings: pd.DataFrame,
    statistical_findings: pd.DataFrame,
    ml_findings: pd.DataFrame,
    anomalies: pd.DataFrame,
    metrics: dict[str, object],
) -> dict[str, str]:
    paths = {
        "raw_sales": output_dir / "raw_sales.csv",
        "validation_findings": output_dir / "validation_findings.csv",
        "statistical_findings": output_dir / "statistical_findings.csv",
        "ml_findings": output_dir / "ml_findings.csv",
        "anomalies": output_dir / "anomalies.csv",
        "metrics": output_dir / "metrics.json",
    }

    raw_data.to_csv(paths["raw_sales"], index=False)
    validation_findings.to_csv(paths["validation_findings"], index=False)
    statistical_findings.to_csv(paths["statistical_findings"], index=False)
    ml_findings.to_csv(paths["ml_findings"], index=False)
    anomalies.to_csv(paths["anomalies"], index=False)
    paths["metrics"].write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return {key: str(path) for key, path in paths.items()}
