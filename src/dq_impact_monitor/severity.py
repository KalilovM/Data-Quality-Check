from __future__ import annotations

import pandas as pd


def classify_severity(combined_findings: pd.DataFrame) -> pd.DataFrame:
    """Classify findings so business users know what to review first."""
    if combined_findings.empty:
        return combined_findings.assign(severity=pd.Series(dtype="str"))

    result = combined_findings.copy()
    result["severity_score"] = result.apply(_severity_score, axis=1)
    result["severity"] = pd.cut(
        result["severity_score"],
        bins=[-1, 3, 6, float("inf")],
        labels=["low", "medium", "high"],
    ).astype(str)
    return result.sort_values(["severity_score", "row_index"], ascending=[False, True])


def _severity_score(row: pd.Series) -> float:
    score = min(float(row["max_score"]), 8.0)
    score += min(int(row["finding_count"]) - 1, 3) * 0.75

    methods = set(row["methods"])
    if {"validation", "statistical_rules"}.issubset(methods):
        score += 1.0
    if {"validation", "isolation_forest"}.issubset(methods):
        score += 1.0
    if bool(row["has_high_rule"]):
        score += 1.5

    return round(score, 2)
