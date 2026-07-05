from __future__ import annotations

import json

import pandas as pd
from sqlalchemy import create_engine, text


def write_pipeline_outputs(
    database_url: str,
    raw_data: pd.DataFrame,
    anomalies: pd.DataFrame,
    metrics: dict[str, object],
) -> None:
    """Persist the latest run to PostgreSQL tables for dashboard or BI use."""
    engine = create_engine(database_url)

    with engine.begin() as connection:
        raw_data.to_sql("sales_kpi_daily", connection, if_exists="replace", index=False)
        anomalies.to_sql("dq_anomalies", connection, if_exists="replace", index=False)
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS dq_run_metrics (
                    id SERIAL PRIMARY KEY,
                    metrics_json JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text("INSERT INTO dq_run_metrics (metrics_json) VALUES (:metrics_json)"),
            {"metrics_json": json.dumps(metrics)},
        )
