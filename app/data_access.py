"""Read analytics tables from DuckDB or Snowflake, with CSV fallback for demos."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = ROOT / "data" / "banking_dw.duckdb"
SOURCE = os.getenv("DATA_SOURCE", "duckdb").strip().lower()

SNOWFLAKE_TABLES = {
    "analytics.loan_features": "RAW.MART_LOAN_FEATURES",
    "analytics.model_scores": "RAW.MART_MODEL_SCORES",
    "analytics.loan_segments": "RAW.MART_LOAN_SEGMENTS",
    "analytics.loan_risk_dashboard": "RAW.MART_LOAN_RISK",
}


def data_source_label() -> str:
    if SOURCE != "snowflake":
        return "DuckDB"
    return "Snowflake" if os.getenv("SNOWFLAKE_PAT") else "Snowflake (PAT missing)"


def snowflake_enabled() -> bool:
    return SOURCE == "snowflake"


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    if not DB.exists():
        raise FileNotFoundError(f"Local database not built: {DB}")
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return con.execute(sql, params or []).fetchdf()
    finally:
        con.close()


@st.cache_resource(show_spinner=False)
def snowflake_connection():
    import snowflake.connector

    token = os.getenv("SNOWFLAKE_PAT")
    if not token:
        raise RuntimeError(
            "SNOWFLAKE_PAT is not set. Add it to .env or set DATA_SOURCE=duckdb."
        )
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="PROGRAMMATIC_ACCESS_TOKEN",
        token=token,
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "PBI_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "LOAN_DEFAULT_DW"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "RAW"),
    )


def snowflake_query(sql: str, params: list | None = None) -> pd.DataFrame:
    con = snowflake_connection()
    cursor = con.cursor()
    try:
        cursor.execute(sql, params or [])
        return cursor.fetch_pandas_all()
    finally:
        cursor.close()


def read_table(table: str, fallback: Path | None = None) -> pd.DataFrame:
    if snowflake_enabled() and table in SNOWFLAKE_TABLES:
        try:
            return snowflake_query(f"SELECT * FROM {SNOWFLAKE_TABLES[table]}")
        except Exception as exc:
            st.warning(f"Snowflake read failed for {table}: {exc}. Using local data.")

    try:
        return query(f"SELECT * FROM {table}")
    except Exception:
        if fallback is not None and fallback.exists():
            return pd.read_csv(fallback)
        raise


def table_counts() -> pd.DataFrame:
    tables = ["dim_date", "dim_branch", "dim_customer", "dim_account", "dim_loan_type", "fact_loans", "fact_transactions"]
    rows = []
    for table in tables:
        count = query(f"SELECT count(*) AS rows FROM mart.{table}").iloc[0]["rows"]
        rows.append({"table": table, "rows": int(count)})
    return pd.DataFrame(rows)


def transactions_for_audit() -> pd.DataFrame:
    return query("SELECT account_id, date_id FROM mart.fact_transactions")


def snowflake_leakage() -> pd.DataFrame:
    return snowflake_query(
        """
        SELECT
            f.loan_id,
            f.account_id,
            TO_NUMBER(TO_CHAR(f.parsed_date, 'YYMMDD')) AS cutoff,
            f.n_txn,
            COUNT_IF(
                t.trans_date < TO_NUMBER(TO_CHAR(f.parsed_date, 'YYMMDD'))
            ) AS used,
            COUNT(t.trans_date) AS total
        FROM RAW.MART_LOAN_FEATURES f
        LEFT JOIN RAW.RAW_TRANS t
            ON t.account_id = f.account_id
        GROUP BY f.loan_id, f.account_id, f.parsed_date, f.n_txn
        ORDER BY f.loan_id
        """
    )
