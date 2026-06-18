from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add KPI features that make anomaly detection more meaningful."""
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")

    safe_customers = result["customer_count"].replace(0, np.nan)
    safe_units = result["units_sold"].replace(0, np.nan)

    result["revenue_per_customer"] = result["revenue"] / safe_customers
    result["return_rate"] = result["returns"] / safe_units
    result["average_unit_revenue"] = result["revenue"] / safe_units
    result["day_of_week"] = result["date"].dt.dayofweek
    result["is_weekend"] = result["day_of_week"].isin([5, 6]).astype(int)

    result = result.sort_values(["store_id", "product_category", "date"], na_position="last")
    group_columns = ["store_id", "product_category"]
    revenue_by_group = result.groupby(group_columns, dropna=False)["revenue"]
    result["rolling_7d_revenue_mean"] = revenue_by_group.transform(
        lambda values: values.shift(1).rolling(7, min_periods=3).mean()
    )
    result["rolling_7d_revenue_std"] = revenue_by_group.transform(
        lambda values: values.shift(1).rolling(7, min_periods=3).std()
    )

    result["rolling_7d_revenue_mean"] = result["rolling_7d_revenue_mean"].fillna(
        result["revenue"].median()
    )
    result["rolling_7d_revenue_std"] = result["rolling_7d_revenue_std"].replace(0, np.nan)
    result["rolling_7d_revenue_std"] = result["rolling_7d_revenue_std"].fillna(
        result["revenue"].std()
    )
    result["revenue_vs_rolling_mean"] = (
        result["revenue"] - result["rolling_7d_revenue_mean"]
    ) / result["rolling_7d_revenue_std"]

    return result.sort_index()
