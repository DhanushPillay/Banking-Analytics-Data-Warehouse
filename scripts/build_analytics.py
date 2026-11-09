"""Load frozen model and analysis outputs into the local DuckDB analytics schema."""
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "banking_dw.duckdb"
ARTIFACTS = ROOT / "artifacts"

TABLES = {
    "model_scores": ARTIFACTS / "metrics" / "model_scores.csv",
    "cv_comparison": ARTIFACTS / "metrics" / "cv_comparison.csv",
    "metrics_comparison": ARTIFACTS / "metrics" / "metrics_comparison.csv",
    "tuning_results": ARTIFACTS / "metrics" / "tuning_results.csv",
    "capacity_model_comparison": ARTIFACTS / "metrics" / "capacity_model_comparison.csv",
    "capacity_model_fold_results": ARTIFACTS / "metrics" / "capacity_model_fold_results.csv",
    "loan_segments": ARTIFACTS / "segments" / "loan_segments.csv",
    "segment_profiles": ARTIFACTS / "segments" / "segment_profiles.csv",
    "pattern_itemsets": ARTIFACTS / "rules" / "pattern_itemsets.csv",
    "pattern_rules": ARTIFACTS / "rules" / "pattern_rules.csv",
    "loan_risk_dashboard": ARTIFACTS / "features" / "loan_risk_dashboard.csv",
    "advanced_metrics": ARTIFACTS / "metrics" / "advanced_metrics.csv",
    "advanced_scores": ARTIFACTS / "metrics" / "advanced_scores.csv",
    "cba_rules": ARTIFACTS / "rules" / "cba_rules.csv",
    "cluster_labels": ARTIFACTS / "segments" / "cluster_labels.csv",
    "cluster_profiles": ARTIFACTS / "segments" / "cluster_profiles.csv",
}


def main() -> None:
    con = duckdb.connect(str(DB))
    con.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    for table, path in TABLES.items():
        if not path.exists():
            print(f"skip {table}: {path} missing")
            continue
        frame = pd.read_csv(path)
        con.register(f"frame_{table}", frame)
        con.execute(
            f"CREATE OR REPLACE TABLE analytics.{table} AS "
            f"SELECT * FROM frame_{table}"
        ).fetchall()
        con.unregister(f"frame_{table}")
        rows = con.execute(f"SELECT count(*) FROM analytics.{table}").fetchall()[0][0]
        print(f"{table}: {rows} rows")
    con.execute("CHECKPOINT")
    con.close()


if __name__ == "__main__":
    main()
