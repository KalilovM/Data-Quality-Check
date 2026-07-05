from __future__ import annotations


def add_spark_validation_flags(spark_frame):
    """Optional PySpark version of the main validation checks.

    This helper is not used by the local pipeline. It shows how the same checks
    can move to Spark when the data becomes too large for a single machine.
    """
    from pyspark.sql import functions as F

    return (
        spark_frame.withColumn(
            "has_missing_critical_field",
            F.col("transaction_id").isNull()
            | F.col("date").isNull()
            | F.col("store_id").isNull()
            | F.col("product_category").isNull()
            | F.col("revenue").isNull(),
        )
        .withColumn("has_negative_revenue", F.col("revenue") < 0)
        .withColumn("has_invalid_discount", ~F.col("discount_rate").between(0, 0.9))
        .withColumn("has_invalid_payment_rate", ~F.col("payment_success_rate").between(0, 1))
        .withColumn("has_high_returns", F.col("returns") > F.col("units_sold"))
        .withColumn(
            "has_data_quality_issue",
            F.col("has_missing_critical_field")
            | F.col("has_negative_revenue")
            | F.col("has_invalid_discount")
            | F.col("has_invalid_payment_rate")
            | F.col("has_high_returns"),
        )
    )
