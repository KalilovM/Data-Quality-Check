from __future__ import annotations

import numpy as np
import pandas as pd

from dq_impact_monitor.config import PipelineConfig

CATEGORIES = ["Electronics", "Home", "Beauty", "Sports", "Grocery"]
REGIONS = ["North", "South", "East", "West"]


def generate_sales_data(config: PipelineConfig) -> pd.DataFrame:
    """Create synthetic daily KPI data with a clear anomaly ground truth."""
    rng = np.random.default_rng(config.seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=config.days, freq="D")
    category_base_units = {
        "Electronics": 42,
        "Home": 58,
        "Beauty": 75,
        "Sports": 50,
        "Grocery": 120,
    }
    category_price = {
        "Electronics": 210.0,
        "Home": 85.0,
        "Beauty": 35.0,
        "Sports": 65.0,
        "Grocery": 12.0,
    }

    rows: list[dict[str, object]] = []
    transaction_number = 1

    for store_number in range(1, config.stores + 1):
        store_factor = rng.normal(1.0, 0.12)
        region = REGIONS[(store_number - 1) % len(REGIONS)]

        for date in dates:
            day_factor = 1.18 if date.dayofweek in {4, 5} else 1.0
            monthly_factor = 1.0 + 0.08 * np.sin((date.day / 31) * 2 * np.pi)

            for category in CATEGORIES:
                base_units = (
                    category_base_units[category]
                    * store_factor
                    * day_factor
                    * monthly_factor
                )
                units_sold = max(1, int(rng.normal(base_units, base_units * 0.14)))
                unit_price = max(
                    1.0,
                    rng.normal(category_price[category], category_price[category] * 0.08),
                )
                discount_rate = float(np.clip(rng.beta(2, 14), 0, 0.45))
                customer_count = max(1, int(units_sold * rng.uniform(0.55, 0.95)))
                returns = int(np.clip(rng.poisson(units_sold * 0.025), 0, units_sold))
                payment_success_rate = float(np.clip(rng.normal(0.985, 0.008), 0.90, 1.0))
                revenue = round(units_sold * unit_price * (1 - discount_rate), 2)

                rows.append(
                    {
                        "transaction_id": f"TX-{transaction_number:08d}",
                        "date": date.date().isoformat(),
                        "store_id": f"S{store_number:03d}",
                        "region": region,
                        "product_category": category,
                        "units_sold": units_sold,
                        "unit_price": round(unit_price, 2),
                        "discount_rate": round(discount_rate, 4),
                        "customer_count": customer_count,
                        "returns": returns,
                        "payment_success_rate": round(payment_success_rate, 4),
                        "revenue": revenue,
                        "is_injected_anomaly": False,
                        "anomaly_type": "normal",
                    }
                )
                transaction_number += 1

    frame = pd.DataFrame(rows)
    return inject_anomalies(frame, config, rng)


def inject_anomalies(
    frame: pd.DataFrame,
    config: PipelineConfig,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Inject business and data quality issues so the monitor can be measured."""
    result = frame.copy()
    anomaly_count = max(1, int(len(result) * config.anomaly_fraction))
    selected_indexes = rng.choice(result.index.to_numpy(), size=anomaly_count, replace=False)
    anomaly_types = np.array(
        [
            "revenue_spike",
            "revenue_drop",
            "negative_revenue",
            "invalid_discount",
            "payment_drop",
            "high_returns",
            "missing_store_id",
            "duplicate_transaction_id",
        ]
    )

    for row_index, anomaly_type in zip(
        selected_indexes,
        rng.choice(anomaly_types, size=anomaly_count, replace=True),
        strict=False,
    ):
        result.loc[row_index, "is_injected_anomaly"] = True
        result.loc[row_index, "anomaly_type"] = anomaly_type

        if anomaly_type == "revenue_spike":
            current_revenue = float(result.loc[row_index, "revenue"])
            result.loc[row_index, "revenue"] = round(current_revenue * 4.5, 2)
        elif anomaly_type == "revenue_drop":
            current_revenue = float(result.loc[row_index, "revenue"])
            result.loc[row_index, "revenue"] = round(current_revenue * 0.06, 2)
        elif anomaly_type == "negative_revenue":
            result.loc[row_index, "revenue"] = -abs(float(result.loc[row_index, "revenue"]))
        elif anomaly_type == "invalid_discount":
            result.loc[row_index, "discount_rate"] = 1.35
        elif anomaly_type == "payment_drop":
            result.loc[row_index, "payment_success_rate"] = round(float(rng.uniform(0.40, 0.70)), 4)
        elif anomaly_type == "high_returns":
            units_sold = int(result.loc[row_index, "units_sold"])
            result.loc[row_index, "returns"] = max(units_sold, int(units_sold * 0.65))
        elif anomaly_type == "missing_store_id":
            result.loc[row_index, "store_id"] = np.nan
        elif anomaly_type == "duplicate_transaction_id" and row_index > 0:
            duplicate_source_index = row_index - 1
            result.loc[row_index, "transaction_id"] = result.loc[
                duplicate_source_index,
                "transaction_id",
            ]
            result.loc[duplicate_source_index, "is_injected_anomaly"] = True
            result.loc[duplicate_source_index, "anomaly_type"] = "duplicate_transaction_id"

    return result
