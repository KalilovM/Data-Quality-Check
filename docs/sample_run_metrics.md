# Sample Run Metrics

Sample local run from July 13, 2026.

Command:

```bash
python scripts/run_pipeline.py --days 90 --stores 12 --output-dir artifacts
```

## Summary

| Metric | Value |
| --- | ---: |
| Records processed | 5,400 |
| Anomalies detected | 658 |
| Processing seconds | 0.7986 |
| High severity | 312 |
| Medium severity | 187 |
| Low severity | 159 |

## Method Comparison

| Method | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| Validation | 1.0000 | 0.5257 | 0.6891 |
| Statistical rules | 0.9056 | 0.5318 | 0.6701 |
| Isolation Forest | 0.6088 | 0.5400 | 0.5724 |
| Combined | 0.7204 | 0.9733 | 0.8279 |

## Anomaly Type Recall

| Anomaly type | Recall |
| --- | ---: |
| Duplicate transaction id | 0.9913 |
| High returns | 1.0000 |
| Invalid discount | 1.0000 |
| Missing store id | 1.0000 |
| Negative revenue | 1.0000 |
| Payment drop | 1.0000 |
| Revenue drop | 0.8182 |
| Revenue spike | 0.9649 |
| Overall | 0.9733 |
