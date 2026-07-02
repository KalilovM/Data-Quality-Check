from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ARTIFACT_DIR = Path("artifacts")

st.set_page_config(page_title="Data Quality Impact Monitor", layout="wide")
st.title("Data Quality Impact Monitor")

metrics_path = ARTIFACT_DIR / "metrics.json"
anomalies_path = ARTIFACT_DIR / "anomalies.csv"

if not metrics_path.exists() or not anomalies_path.exists():
    st.info("Run `python scripts/run_pipeline.py` first to generate dashboard data.")
    st.stop()

metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
anomalies = pd.read_csv(anomalies_path)

left, middle, right = st.columns(3)
left.metric("Records processed", metrics["records_processed"])
middle.metric("Anomalies detected", metrics["anomalies_detected"])
right.metric("Processing seconds", metrics["processing_seconds"])

st.subheader("Detection Performance")
performance = pd.DataFrame(metrics["method_metrics"]).T
st.dataframe(performance, width="stretch")

st.subheader("Severity Mix")
severity_counts = pd.Series(metrics["severity_counts"], name="count")
st.bar_chart(severity_counts)

st.subheader("Anomaly Type Recall")
recall = pd.Series(metrics["anomaly_type_recall"], name="recall")
st.dataframe(recall, width="stretch")

st.subheader("Detected Anomalies")
display_columns = [
    "date",
    "store_id",
    "product_category",
    "revenue",
    "units_sold",
    "payment_success_rate",
    "anomaly_type",
    "severity",
    "methods",
    "rules",
]
st.dataframe(anomalies[display_columns], width="stretch")
