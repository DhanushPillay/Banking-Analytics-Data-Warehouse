"""Rebuild the whole local warehouse: raw CSV -> mart -> feature mart -> analytics."""
from pathlib import Path

import duckdb

from build_advanced_models import main as build_advanced
from build_analytics import main as build_analytics
from etl_pipeline import extract_data, load_data, transform_dimensions, transform_facts

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "banking_dw.duckdb"
FEATURE_SQL = ROOT / "sql" / "local" / "03_feature_mart.sql"


def validate() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    checks = {
        "fact_loans": "SELECT count(*) FROM mart.fact_loans",
        "fact_transactions": "SELECT count(*) FROM mart.fact_transactions",
        "dim_customer": "SELECT count(*) FROM mart.dim_customer",
        "loan features": "SELECT count(*) FROM analytics.loan_features",
        "defaults": "SELECT sum(target) FROM analytics.loan_features",
        "features with post-loan rows": (
            "SELECT count(*) FROM analytics.loan_features f "
            "WHERE f.n_txn <> ("
            "  SELECT count(*) FROM mart.fact_transactions t "
            "  WHERE t.account_id = f.account_id AND t.date_id < f.loan_date_id"
            ")"
        ),
    }
    for label, sql in checks.items():
        value = con.execute(sql).fetchone()[0]
        print(f"{label}: {value}")
    con.close()


def main() -> None:
    print("Extracting raw CSVs...")
    raw = extract_data(str(ROOT / "data"))
    dims = transform_dimensions(raw)
    facts = transform_facts(raw, dims)
    load_data(dims, facts)

    print("Building feature mart...")
    con = duckdb.connect(str(DB))
    con.execute(FEATURE_SQL.read_text(encoding="utf-8"))
    con.execute("CHECKPOINT")
    con.close()

    print("Training advanced models...")
    build_advanced()

    print("Loading saved analytics outputs...")
    build_analytics()

    print("Validating...")
    validate()


if __name__ == "__main__":
    main()
