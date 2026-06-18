from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

STATISTICAL_FEATURES = [
    "revenue",
    "units_sold",
    "revenue_per_customer",
    "return_rate",
    "payment_success_rate",
    "revenue_vs_rolling_mean",
]

ML_FEATURES = [
    "revenue",
    "units_sold",
    "discount_rate",
    "customer_count",
    "returns",
    "payment_success_rate",
    "revenue_per_customer",
    "return_rate",
    "average_unit_revenue",
    "revenue_vs_rolling_mean",
    "day_of_week",
    "is_weekend",
]


def run_statistical_rules(frame: pd.DataFrame, threshold: float = 5.5) -> pd.DataFrame:
    """Detect unusual KPI values with robust z-score rules."""
    findings: list[pd.DataFrame] = []

    for feature in STATISTICAL_FEATURES:
        values = pd.to_numeric(frame[feature], errors="coerce")
        median = values.median()
        mad = (values - median).abs().median()
        if pd.isna(mad) or mad == 0:
            continue

        robust_z = 0.6745 * (values - median) / mad
        mask = robust_z.abs() >= threshold
        if mask.any():
            findings.append(
                pd.DataFrame(
                    {
                        "row_index": frame.index[mask].astype(int),
                        "method": "statistical_rules",
                        "rule_name": f"{feature}_robust_z",
                        "base_severity": "medium",
                        "score": robust_z.loc[mask].abs().round(4),
                    }
                )
            )

    business_masks = [
        ("payment_success_rate_drop", frame["payment_success_rate"] < 0.75, 4.5),
        ("high_return_rate", frame["return_rate"] > 0.35, 4.5),
    ]
    for rule_name, mask, score in business_masks:
        if mask.any():
            findings.append(
                pd.DataFrame(
                    {
                        "row_index": frame.index[mask].astype(int),
                        "method": "statistical_rules",
                        "rule_name": rule_name,
                        "base_severity": "medium",
                        "score": score,
                    }
                )
            )

    revenue_drop_mask = (
        (frame["revenue"] < frame["rolling_7d_revenue_mean"] * 0.25)
        & (frame["revenue_vs_rolling_mean"] < -2.0)
    )
    if revenue_drop_mask.any():
        findings.append(
            pd.DataFrame(
                {
                    "row_index": frame.index[revenue_drop_mask].astype(int),
                    "method": "statistical_rules",
                    "rule_name": "revenue_drop_vs_recent_history",
                    "base_severity": "medium",
                    "score": frame.loc[revenue_drop_mask, "revenue_vs_rolling_mean"]
                    .abs()
                    .round(4),
                }
            )
        )

    if not findings:
        return _empty_findings()

    return pd.concat(findings, ignore_index=True).sort_values(["row_index", "rule_name"])


def run_isolation_forest(
    frame: pd.DataFrame,
    contamination: float,
    seed: int,
) -> pd.DataFrame:
    """Detect multi-feature outliers with Isolation Forest."""
    matrix = frame[ML_FEATURES].replace([np.inf, -np.inf], np.nan)
    matrix = matrix.apply(pd.to_numeric, errors="coerce")
    matrix = matrix.fillna(matrix.median(numeric_only=True))

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=seed,
    )
    labels = model.fit_predict(matrix)
    anomaly_mask = labels == -1

    if not anomaly_mask.any():
        return _empty_findings()

    scores = -model.score_samples(matrix)
    return pd.DataFrame(
        {
            "row_index": frame.index[anomaly_mask].astype(int),
            "method": "isolation_forest",
            "rule_name": "multivariate_outlier",
            "base_severity": "medium",
            "score": np.round(scores[anomaly_mask], 4),
        }
    ).sort_values("row_index")


def combine_findings(*finding_frames: pd.DataFrame) -> pd.DataFrame:
    usable_frames = [frame for frame in finding_frames if not frame.empty]
    if not usable_frames:
        return pd.DataFrame(
            columns=[
                "row_index",
                "methods",
                "rules",
                "max_score",
                "finding_count",
                "has_high_rule",
            ],
        )

    all_findings = pd.concat(usable_frames, ignore_index=True)
    grouped = (
        all_findings.groupby("row_index")
        .agg(
            methods=("method", lambda values: sorted(set(values))),
            rules=("rule_name", lambda values: sorted(set(values))),
            max_score=("score", "max"),
            finding_count=("rule_name", "count"),
            has_high_rule=("base_severity", lambda values: "high" in set(values)),
        )
        .reset_index()
    )
    return grouped.sort_values("row_index")


def _empty_findings() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["row_index", "method", "rule_name", "base_severity", "score"],
    )
