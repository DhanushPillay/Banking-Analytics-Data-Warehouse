"""Upload local CSVs to Snowflake with write_pandas. Creds via env, never in repo.

Required env: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD (or PRIVATE_KEY_FILE),
  SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE= PBI_WH, SNOWFLAKE_DATABASE=LOAN_DEFAULT_DW
Optional: SNOWFLAKE_SCHEMA=RAW
"""
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

ROOT = Path(__file__).resolve().parents[1]
FILES = {  # csv path -> (table, sep)
    "data/loan.csv": ("RAW_LOAN", ";"),
    "data/trans.csv": ("RAW_TRANS", ";"),
    "data/client.csv": ("RAW_CLIENT", ";"),
    "data/account.csv": ("RAW_ACCOUNT", ";"),
    "data/disp.csv": ("RAW_DISP", ";"),
    "data/loan_features.csv": ("MART_LOAN_FEATURES", ","),
    "outputs/model_scores.csv": ("MART_MODEL_SCORES", ","),
    "outputs/loan_segments.csv": ("MART_LOAN_SEGMENTS", ","),
    "outputs/loan_risk_dashboard.csv": ("MART_LOAN_RISK", ","),
}

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ.get("SNOWFLAKE_PASSWORD"),
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "PBI_WH"),
    database=os.environ.get("SNOWFLAKE_DATABASE", "LOAN_DEFAULT_DW"),
    schema=os.environ.get("SNOWFLAKE_SCHEMA", "RAW"),
)
for rel, (table, sep) in FILES.items():
    df = pd.read_csv(ROOT / rel, sep=sep, low_memory=False)
    ok, _, nrows, _ = write_pandas(conn, df, table.upper(), auto_create_table=False)
    assert ok, table
    print(f"{table}: {nrows} rows")
conn.close()
print("upload complete")
