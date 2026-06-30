from __future__ import annotations

import pandas as pd

from dq_impact_monitor.validation import validate_sales_data


def test_validate_sales_data_flags_common_quality_issues() -> None:
    frame = pd.DataFrame(
        [
            {
                "transaction_id": "TX-1",
                "date": "2026-01-01",
                "store_id": "S001",
                "product_category": "Home",
                "units_sold": 10,
                "discount_rate": 0.1,
                "payment_success_rate": 0.99,
                "returns": 0,
                "revenue": 100.0,
            },
            {
                "transaction_id": "TX-1",
                "date": "2026-01-01",
                "store_id": None,
                "product_category": "Home",
                "units_sold": 10,
                "discount_rate": 1.2,
                "payment_success_rate": 0.99,
                "returns": 12,
                "revenue": -50.0,
            },
        ]
    )

    findings = validate_sales_data(frame)

    assert "missing_store_id" in set(findings["rule_name"])
    assert "negative_revenue" in set(findings["rule_name"])
    assert "invalid_discount_rate" in set(findings["rule_name"])
    assert "returns_above_units_sold" in set(findings["rule_name"])
    assert "duplicate_transaction_id" in set(findings["rule_name"])
