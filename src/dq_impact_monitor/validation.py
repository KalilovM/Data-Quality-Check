from __future__ import annotations

import pandas as pd

CRITICAL_COLUMNS = ["transaction_id", "date", "store_id", "product_category", "revenue"]


def validate_sales_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Return row-level validation findings with business-friendly rule names."""
    findings: list[pd.DataFrame] = []

    def add_findings(mask: pd.Series, rule_name: str, severity: str, score: float) -> None:
        flagged = frame.loc[mask.fillna(False)].copy()
        if flagged.empty:
            return
        findings.append(
            pd.DataFrame(
                {
                    "row_index": flagged.index.astype(int),
                    "method": "validation",
                    "rule_name": rule_name,
                    "base_severity": severity,
                    "score": score,
                }
            )
        )

    for column in CRITICAL_COLUMNS:
        if column in frame.columns:
            add_findings(frame[column].isna(), f"missing_{column}", "high", 5.0)

    add_findings(frame["revenue"] < 0, "negative_revenue", "high", 5.0)
    add_findings(frame["units_sold"] <= 0, "non_positive_units", "high", 5.0)
    add_findings(~frame["discount_rate"].between(0, 0.9), "invalid_discount_rate", "medium", 4.0)
    add_findings(~frame["payment_success_rate"].between(0, 1), "invalid_payment_rate", "high", 5.0)
    add_findings(frame["returns"] > frame["units_sold"], "returns_above_units_sold", "high", 5.0)
    add_findings(
        frame.duplicated("transaction_id", keep=False),
        "duplicate_transaction_id",
        "medium",
        3.5,
    )

    if not findings:
        return _empty_findings()

    return pd.concat(findings, ignore_index=True).sort_values(["row_index", "rule_name"])


def _empty_findings() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["row_index", "method", "rule_name", "base_severity", "score"],
    )
