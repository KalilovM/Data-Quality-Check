from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Data Quality Impact Monitor.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--stores", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--anomaly-fraction", type=float, default=0.08)
    parser.add_argument("--isolation-contamination", type=float, default=0.08)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    return parser.parse_args()


def main() -> None:
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from dq_impact_monitor.config import PipelineConfig
    from dq_impact_monitor.pipeline import run_pipeline

    args = parse_args()
    config = PipelineConfig(
        days=args.days,
        stores=args.stores,
        seed=args.seed,
        anomaly_fraction=args.anomaly_fraction,
        isolation_contamination=args.isolation_contamination,
        output_dir=args.output_dir,
    )
    result = run_pipeline(config)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
