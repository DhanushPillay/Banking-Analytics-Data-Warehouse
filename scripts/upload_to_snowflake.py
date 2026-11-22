"""Upload local CSVs to Snowflake with write_pandas. Creds via .env, never in repo.

Required env: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_ROLE,
  SNOWFLAKE_WAREHOUSE=PBI_WH, SNOWFLAKE_DATABASE=LOAN_DEFAULT_DW
Auth: SNOWFLAKE_PAT, or SNOWFLAKE_PASSWORD with optional TOTP prompt.

Raw extracts go to RAW; modelled tables go to MART. Each target table is
truncated before loading, so rerunning the upload is idempotent.

The DDL creates the target tables. This script renames the few CSV columns that
differ from the DDL, drops the extra date column in the risk table, and checks
every column against Snowflake before writing. It never creates tables.
"""
import getpass
import os
from pathlib import Path

import duckdb
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.errors import DatabaseError
from snowflake.connector.pandas_tools import write_pandas

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

FILES = {  # csv path -> (table, schema, sep, renames, drop)
    "data/loan.csv": ("RAW_LOAN", "RAW", ";", {"date": "loan_date"}, []),
    "data/trans.csv": ("RAW_TRANS", "RAW", ";", {"date": "trans_date"}, []),
    "data/client.csv": ("RAW_CLIENT", "RAW", ";", {}, []),
    "data/account.csv": ("RAW_ACCOUNT", "RAW", ";", {"date": "open_date"}, []),
    "data/disp.csv": ("RAW_DISP", "RAW", ";", {}, []),
    "data/features/loan_features.csv": (
        "MART_LOAN_FEATURES",
        "MART",
        ",",
        {"date": "loan_date"},
        [],
    ),
    "artifacts/metrics/model_scores.csv": (
        "MART_MODEL_SCORES",
        "MART",
        ",",
        {},
        [],
    ),
    "artifacts/segments/loan_segments.csv": (
        "MART_LOAN_SEGMENTS",
        "MART",
        ",",
        {},
        [],
    ),
    "artifacts/features/loan_risk_dashboard.csv": (
        "MART_LOAN_RISK",
        "MART",
        ",",
        {},
        ["date"],
    ),
    "artifacts/segments/cluster_labels.csv": (
        "MART_CLUSTER_LABELS",
        "MART",
        ",",
        {},
        [],
    ),
    "artifacts/metrics/clustering_comparison.csv": (
        "MART_CLUSTERING_COMPARISON",
        "MART",
        ",",
        {},
        [],
    ),
}

DUCKDB_PATH = ROOT / "data" / "banking_dw.duckdb"

WAREHOUSE_TABLES = {  # Snowflake table -> query against the local star schema
    "DIM_DATE": """
        SELECT date_id, CAST(full_date AS DATE) AS full_date, day, month,
               month_name, quarter, year, day_of_week, is_weekend
        FROM mart.dim_date
    """,
    "DIM_BRANCH": "SELECT * FROM mart.dim_branch",
    "DIM_CUSTOMER": """
        SELECT customer_id, first_name, last_name, gender, gender_bin, age,
               CAST(age_group AS VARCHAR) AS age_group, city, home_branch_id,
               customer_segment, CAST(account_open_date AS DATE) AS account_open_date
        FROM mart.dim_customer
    """,
    "DIM_ACCOUNT": """
        SELECT account_id, customer_id, account_type,
               CAST(open_date AS DATE) AS open_date, status
        FROM mart.dim_account
    """,
    "DIM_LOAN_TYPE": "SELECT * FROM mart.dim_loan_type",
    "FACT_LOANS": "SELECT * FROM mart.fact_loans",
    "FACT_TRANSACTIONS": "SELECT * FROM mart.fact_transactions",
}

database = os.environ.get("SNOWFLAKE_DATABASE", "LOAN_DEFAULT_DW")
session_schema = os.environ.get("SNOWFLAKE_SCHEMA", "RAW")


def connect_snowflake():
    options = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.environ["SNOWFLAKE_ROLE"],
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "PBI_WH"),
        "database": database,
        "schema": session_schema,
    }
    pat = os.environ.get("SNOWFLAKE_PAT")
    if pat:
        return snowflake.connector.connect(
            **options,
            authenticator="PROGRAMMATIC_ACCESS_TOKEN",
            token=pat,
        )
    password = os.environ.get("SNOWFLAKE_PASSWORD") or getpass.getpass(
        f"Snowflake password for {os.environ['SNOWFLAKE_USER']}: "
    )
    options["password"] = password
    try:
        return snowflake.connector.connect(**options)
    except DatabaseError as exc:
        if "MFA" not in str(exc).upper():
            raise
        code = os.environ.get("SNOWFLAKE_MFA_CODE") or getpass.getpass(
            "Snowflake MFA code (6 digits): "
        )
        return snowflake.connector.connect(
            **options,
            authenticator="username_password_mfa",
            passcode=code,
        )


def load_frame(conn, cursor, df, table, target_schema) -> None:
    df = df.copy()
    df.columns = [str(column).upper() for column in df.columns]
    cursor.execute(
        f"SELECT COLUMN_NAME FROM {database}.INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
        (target_schema, table),
    )
    expected = [row[0] for row in cursor.fetchall()]
    missing = set(expected) - set(df.columns)
    extra = set(df.columns) - set(expected)
    if missing or extra:
        raise SystemExit(
            f"{target_schema}.{table}: missing={sorted(missing)} "
            f"extra={sorted(extra)}"
        )

    cursor.execute(f"TRUNCATE TABLE IF EXISTS {database}.{target_schema}.{table}")
    ok, _, nrows, _ = write_pandas(
        conn,
        df,
        table,
        schema=target_schema,
        chunk_size=100_000,
        auto_create_table=False,
    )
    if not ok:
        raise SystemExit(f"{target_schema}.{table}: write failed")
    print(f"{target_schema}.{table}: {nrows} rows")


def main() -> None:
    conn = connect_snowflake()
    try:
        cursor = conn.cursor()
        for rel, (table, target_schema, sep, renames, drop) in FILES.items():
            df = pd.read_csv(ROOT / rel, sep=sep, low_memory=False)
            df = df.rename(columns=renames).drop(columns=drop, errors="ignore")
            df.columns = [str(column).upper() for column in df.columns]
            if "PARSED_DATE" in df.columns:
                df["PARSED_DATE"] = pd.to_datetime(
                    df["PARSED_DATE"], errors="coerce"
                ).dt.date
            load_frame(conn, cursor, df, table, target_schema)

        duck = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        try:
            for table, query in WAREHOUSE_TABLES.items():
                df = duck.execute(query).fetchdf()
                for column in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[column]):
                        df[column] = df[column].dt.date
                load_frame(conn, cursor, df, table, "MART")
        finally:
            duck.close()
    finally:
        conn.close()
    print("upload complete")


if __name__ == "__main__":
    main()
