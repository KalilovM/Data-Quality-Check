from __future__ import annotations

import pandas as pd


def classification_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float | int]:
    truth = y_true.astype(bool)
    predicted = y_pred.astype(bool)

    true_positive = int((truth & predicted).sum())
    false_positive = int((~truth & predicted).sum())
    false_negative = int((truth & ~predicted).sum())
    true_negative = int((~truth & ~predicted).sum())

    precision = _safe_divide(true_positive, true_positive + false_positive)
    recall = _safe_divide(true_positive, true_positive + false_negative)
    f1 = _safe_divide(2 * precision * recall, precision + recall)

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def anomaly_type_recall(frame: pd.DataFrame, predicted_indexes: set[int]) -> dict[str, float]:
    detected = frame.index.isin(predicted_indexes)
    result: dict[str, float] = {}

    anomaly_frame = frame.loc[frame["is_injected_anomaly"]]
    for anomaly_type, group in anomaly_frame.groupby("anomaly_type"):
        recall = group.index.isin(predicted_indexes).sum() / len(group)
        result[str(anomaly_type)] = round(float(recall), 4)

    result["overall"] = round(float(detected[frame["is_injected_anomaly"]].mean()), 4)
    return dict(sorted(result.items()))


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
