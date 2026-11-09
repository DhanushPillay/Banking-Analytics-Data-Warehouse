# Banking Data Warehouse on Snowflake

> **Status:** This is the older manual guide. The current loader uses
> `LOAN_DEFAULT_DW` with warehouse `PBI_WH` and schema `RAW`. Run
> `sql/snowflake/ddl_snowflake.sql`, configure `.env`, then run
> `scripts/upload_to_snowflake.py`. Use this guide only for the manual
> `COPY INTO` background; do not copy its database names.

This guide starts after you have already created your Snowflake account. It uses the existing project in this repository and explains exactly what to run and when to run it.

The process has two parts:

1. Create Snowflake objects and load the warehouse.
2. Connect the existing Python transformations to Snowflake.

The first version uses a full refresh, matching the current project behavior: every run replaces the MART tables.

## 1. What You Need

You need:

- Your Snowflake login
- A Snowflake role that can create warehouses, databases, schemas, tables, stages, and file formats
- The repository open in VS Code
- Python installed
- The raw CSV files in `data/`

The project expects these files:

```text
data/client.csv
data/account.csv
data/disp.csv
data/district.csv
data/loan.csv
data/trans.csv
```

The ETL code also supports `.asc` files. It reads semicolon-delimited files.

## 2. Open a Snowflake Worksheet

1. Sign in to Snowflake.
2. Open **Snowsight**.
3. Open **Worksheets**.
4. Select **SQL Worksheet**.
5. Select your administrator or setup role.
6. Paste and run the SQL below.

Run the statements in order. You can select one statement and press **Run**, or run the complete script.

```sql
-- Use the role that is allowed to create these objects.
-- Replace ACCOUNTADMIN with your approved setup role if required.
USE ROLE ACCOUNTADMIN;

-- XS is the smallest warehouse size and is enough for this project.
CREATE WAREHOUSE IF NOT EXISTS BANKING_DW_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS BANKING_DW;

CREATE SCHEMA IF NOT EXISTS BANKING_DW.RAW;
CREATE SCHEMA IF NOT EXISTS BANKING_DW.STAGING;
CREATE SCHEMA IF NOT EXISTS BANKING_DW.MART;

USE WAREHOUSE BANKING_DW_WH;
USE DATABASE BANKING_DW;
USE SCHEMA RAW;

CREATE FILE FORMAT IF NOT EXISTS BANKING_DW.RAW.BANKING_CSV_FORMAT
    TYPE = CSV
    FIELD_DELIMITER = ';'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null')
    ENCODING = 'UTF8'
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

CREATE STAGE IF NOT EXISTS BANKING_DW.RAW.BANKING_STAGE
    FILE_FORMAT = BANKING_DW.RAW.BANKING_CSV_FORMAT;

SHOW WAREHOUSES LIKE 'BANKING_DW_WH';
SHOW STAGES IN SCHEMA BANKING_DW.RAW;
SHOW FILE FORMATS IN SCHEMA BANKING_DW.RAW;
```

### What these objects mean

- `BANKING_DW_WH`: compute used to run SQL.
- `BANKING_DW`: database containing the project.
- `RAW`: source data copied as received.
- `STAGING`: temporary or intermediate data.
- `MART`: final dimensional warehouse tables.
- `BANKING_STAGE`: Snowflake storage for uploaded files.
- `BANKING_CSV_FORMAT`: tells Snowflake how to read the files.

## 3. Upload the Raw CSV Files (Optional)

You said you have already uploaded the seven files from `data/clean`. If that is correct, skip this section and continue at **Section 9: Upload the Clean Files**. You only need this RAW upload if you also want to preserve the original six source files in Snowflake.

In Snowsight:

1. Open **Data**.
2. Open database `BANKING_DW`.
3. Open schema `RAW`.
4. Open **Stages**.
5. Select `BANKING_STAGE`.
6. Select **Add Files** or **Upload Files**.
7. Upload the six files from this repository's `data` folder.
8. Put them inside a folder named `raw/` if Snowsight asks for a path.

After uploading, run:

```sql
LIST @BANKING_DW.RAW.BANKING_STAGE;
```

You should see six files if you uploaded the raw source files. If a file is missing, do not continue with the RAW loading steps.

## 4. Create RAW Tables

Open a new worksheet, or continue in the setup worksheet. Run this SQL:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE BANKING_DW_WH;
USE DATABASE BANKING_DW;
USE SCHEMA RAW;

CREATE OR REPLACE TABLE RAW_CLIENT (
    CLIENT_ID NUMBER,
    BIRTH_NUMBER VARCHAR,
    DISTRICT_ID NUMBER
);

CREATE OR REPLACE TABLE RAW_ACCOUNT (
    ACCOUNT_ID NUMBER,
    DISTRICT_ID NUMBER,
    FREQUENCY VARCHAR,
    DATE VARCHAR
);

CREATE OR REPLACE TABLE RAW_DISP (
    DISP_ID NUMBER,
    CLIENT_ID NUMBER,
    ACCOUNT_ID NUMBER,
    TYPE VARCHAR
);

CREATE OR REPLACE TABLE RAW_DISTRICT (
    DISTRICT_ID NUMBER,
    A2 VARCHAR,
    A3 VARCHAR,
    A4 NUMBER
);

CREATE OR REPLACE TABLE RAW_LOAN (
    LOAN_ID NUMBER,
    ACCOUNT_ID NUMBER,
    DATE VARCHAR,
    AMOUNT NUMBER(12, 2),
    DURATION NUMBER,
    STATUS VARCHAR
);

CREATE OR REPLACE TABLE RAW_TRANS (
    TRANS_ID NUMBER,
    ACCOUNT_ID NUMBER,
    DATE VARCHAR,
    TYPE VARCHAR,
    OPERATION VARCHAR,
    AMOUNT NUMBER(12, 2),
    BALANCE NUMBER(12, 2),
    K_SYMBOL VARCHAR,
    BANK VARCHAR,
    ACCOUNT_PARTNER NUMBER
);
```

The source dataset can contain extra columns depending on its downloaded version. If `COPY INTO` reports a column mismatch, run `DESC TABLE RAW_TRANS` and compare it with the header in `trans.csv`. Add the missing source columns to the RAW table before loading.

## 5. Load RAW Tables

The files uploaded under `raw/` are loaded with these commands:

```sql
USE DATABASE BANKING_DW;
USE SCHEMA RAW;

COPY INTO RAW_CLIENT
FROM @BANKING_STAGE/raw/client.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW_ACCOUNT
FROM @BANKING_STAGE/raw/account.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW_DISP
FROM @BANKING_STAGE/raw/disp.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW_DISTRICT
FROM @BANKING_STAGE/raw/district.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW_LOAN
FROM @BANKING_STAGE/raw/loan.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW_TRANS
FROM @BANKING_STAGE/raw/trans.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';
```

After each `COPY INTO`, inspect the result. Confirm that `rows_loaded` is greater than zero and that the command did not fail.

Check the RAW table counts:

```sql
SELECT 'RAW_CLIENT' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM RAW_CLIENT
UNION ALL
SELECT 'RAW_ACCOUNT', COUNT(*) FROM RAW_ACCOUNT
UNION ALL
SELECT 'RAW_DISP', COUNT(*) FROM RAW_DISP
UNION ALL
SELECT 'RAW_DISTRICT', COUNT(*) FROM RAW_DISTRICT
UNION ALL
SELECT 'RAW_LOAN', COUNT(*) FROM RAW_LOAN
UNION ALL
SELECT 'RAW_TRANS', COUNT(*) FROM RAW_TRANS;
```

## 6. Prepare Python on Windows

Open the VS Code terminal at the repository root:

```powershell
Set-Location 'E:\Personal Projects\banking-dw'

if (-not (Test-Path 'venv')) {
    py -m venv venv
}

.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install snowflake-connector-python snowflake-sqlalchemy
pytest -q tests/test_etl_pipeline.py
```

If PowerShell blocks activation, run this once in a PowerShell terminal opened by you:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Do not put your Snowflake password in this guide or in Python source code.

## 7. Create a Local `.env` File

Create a file named `.env` in the repository root. Do not commit it.

```dotenv
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=BANKING_DW_WH
SNOWFLAKE_DATABASE=BANKING_DW
SNOWFLAKE_SCHEMA=MART
SNOWFLAKE_ROLE=your_snowflake_role
SNOWFLAKE_STAGE=BANKING_DW.RAW.BANKING_STAGE
SNOWFLAKE_STAGE_FOLDER=clean
```

`SNOWFLAKE_ACCOUNT` is the account identifier used by the Snowflake Python connector. It is usually visible in your Snowflake URL. Do not include `https://`.

If your account uses browser or external authentication instead of a password, omit `SNOWFLAKE_PASSWORD` and set:

```dotenv
SNOWFLAKE_AUTHENTICATOR=externalbrowser
```

Add a safe template file named `.env.example` if the repository does not already have one:

```dotenv
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=do_not_put_real_password_here
SNOWFLAKE_AUTHENTICATOR=
SNOWFLAKE_WAREHOUSE=BANKING_DW_WH
SNOWFLAKE_DATABASE=BANKING_DW
SNOWFLAKE_SCHEMA=MART
SNOWFLAKE_ROLE=your_snowflake_role
SNOWFLAKE_STAGE=BANKING_DW.RAW.BANKING_STAGE
SNOWFLAKE_STAGE_FOLDER=clean
```

## 8. Generate the Clean Files

From the repository root, run the transformation functions. The current `main()` also tries to connect to PostgreSQL, so for the first run use this small command instead:

```powershell
python -c "from scripts.etl_pipeline import extract_data, transform_dimensions, transform_facts; import os; raw=extract_data('data'); dims=transform_dimensions(raw); facts=transform_facts(raw, dims); os.makedirs('data/clean', exist_ok=True); [value.to_csv('data/clean/' + name + '.csv', index=False) for name, value in {**dims, **facts}.items()]; print('Clean files created')"
```

Check that these seven files exist:

```powershell
Get-ChildItem data\clean
```

Expected files:

```text
dim_date.csv
dim_branch.csv
dim_customer.csv
dim_account.csv
dim_loan_type.csv
fact_loans.csv
fact_transactions.csv
```

## 9. Upload the Clean Files

This is the step you need because you uploaded seven clean files. The seven files are already transformed by Python and match the MART tables.

In Snowsight, open `BANKING_DW.RAW.BANKING_STAGE` again and upload the seven files into a folder named `clean/`.

Then verify:

```sql
LIST @BANKING_DW.RAW.BANKING_STAGE/clean;
```

## 10. Create MART Tables

Run this Snowflake-compatible version of the project schema:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE BANKING_DW_WH;
USE DATABASE BANKING_DW;
USE SCHEMA MART;

CREATE OR REPLACE TABLE DIM_DATE (
    DATE_ID NUMBER PRIMARY KEY,
    FULL_DATE DATE NOT NULL,
    DAY NUMBER NOT NULL,
    MONTH NUMBER NOT NULL,
    MONTH_NAME VARCHAR(10) NOT NULL,
    QUARTER NUMBER NOT NULL,
    YEAR NUMBER NOT NULL,
    DAY_OF_WEEK VARCHAR(10) NOT NULL,
    IS_WEEKEND BOOLEAN NOT NULL
);

CREATE OR REPLACE TABLE DIM_BRANCH (
    BRANCH_ID NUMBER PRIMARY KEY,
    BRANCH_NAME VARCHAR(100) NOT NULL,
    CITY VARCHAR(50) NOT NULL,
    REGION VARCHAR(50) NOT NULL,
    BRANCH_TYPE VARCHAR(20) NOT NULL
);

CREATE OR REPLACE TABLE DIM_CUSTOMER (
    CUSTOMER_ID NUMBER PRIMARY KEY,
    FIRST_NAME VARCHAR(50) NOT NULL,
    LAST_NAME VARCHAR(50) NOT NULL,
    GENDER VARCHAR(10) NOT NULL,
    AGE NUMBER NOT NULL,
    AGE_GROUP VARCHAR(20) NOT NULL,
    CITY VARCHAR(50) NOT NULL,
    HOME_BRANCH_ID NUMBER NOT NULL,
    CUSTOMER_SEGMENT VARCHAR(20) NOT NULL,
    ACCOUNT_OPEN_DATE DATE NOT NULL,
    CONSTRAINT FK_CUSTOMER_BRANCH FOREIGN KEY (HOME_BRANCH_ID)
        REFERENCES DIM_BRANCH (BRANCH_ID)
);

CREATE OR REPLACE TABLE DIM_ACCOUNT (
    ACCOUNT_ID NUMBER PRIMARY KEY,
    CUSTOMER_ID NUMBER NOT NULL,
    ACCOUNT_TYPE VARCHAR(20) NOT NULL,
    OPEN_DATE DATE NOT NULL,
    STATUS VARCHAR(10) NOT NULL,
    CONSTRAINT FK_ACCOUNT_CUSTOMER FOREIGN KEY (CUSTOMER_ID)
        REFERENCES DIM_CUSTOMER (CUSTOMER_ID)
);

CREATE OR REPLACE TABLE DIM_LOAN_TYPE (
    LOAN_TYPE_ID NUMBER PRIMARY KEY,
    LOAN_TYPE_NAME VARCHAR(30) NOT NULL,
    TYPICAL_RATE_PCT NUMBER(4, 2) NOT NULL
);

CREATE OR REPLACE TABLE FACT_LOANS (
    LOAN_ID NUMBER PRIMARY KEY,
    CUSTOMER_ID NUMBER NOT NULL,
    BRANCH_ID NUMBER NOT NULL,
    LOAN_TYPE_ID NUMBER NOT NULL,
    DATE_ID NUMBER NOT NULL,
    AMOUNT NUMBER(12, 2) NOT NULL,
    INTEREST_RATE NUMBER(4, 2) NOT NULL,
    TENURE_MONTHS NUMBER NOT NULL,
    STATUS VARCHAR(15) NOT NULL,
    CONSTRAINT FK_LOAN_CUSTOMER FOREIGN KEY (CUSTOMER_ID)
        REFERENCES DIM_CUSTOMER (CUSTOMER_ID),
    CONSTRAINT FK_LOAN_BRANCH FOREIGN KEY (BRANCH_ID)
        REFERENCES DIM_BRANCH (BRANCH_ID),
    CONSTRAINT FK_LOAN_TYPE FOREIGN KEY (LOAN_TYPE_ID)
        REFERENCES DIM_LOAN_TYPE (LOAN_TYPE_ID),
    CONSTRAINT FK_LOAN_DATE FOREIGN KEY (DATE_ID)
        REFERENCES DIM_DATE (DATE_ID)
);

CREATE OR REPLACE TABLE FACT_TRANSACTIONS (
    TRANSACTION_ID NUMBER PRIMARY KEY,
    ACCOUNT_ID NUMBER NOT NULL,
    DATE_ID NUMBER NOT NULL,
    BRANCH_ID NUMBER NOT NULL,
    TRANSACTION_TYPE VARCHAR(20) NOT NULL,
    AMOUNT NUMBER(12, 2) NOT NULL,
    CONSTRAINT FK_TRANSACTION_ACCOUNT FOREIGN KEY (ACCOUNT_ID)
        REFERENCES DIM_ACCOUNT (ACCOUNT_ID),
    CONSTRAINT FK_TRANSACTION_DATE FOREIGN KEY (DATE_ID)
        REFERENCES DIM_DATE (DATE_ID),
    CONSTRAINT FK_TRANSACTION_BRANCH FOREIGN KEY (BRANCH_ID)
        REFERENCES DIM_BRANCH (BRANCH_ID)
);
```

Snowflake accepts these constraints for documentation. Always run the validation queries in this guide because standard Snowflake table constraints are generally not enforced like PostgreSQL constraints.

## 11. Load MART Tables Directly from Clean CSV Files

For a first manual load, use temporary file formats that skip the clean-file headers:

```sql
USE DATABASE BANKING_DW;
USE SCHEMA MART;

CREATE OR REPLACE FILE FORMAT BANKING_DW.RAW.CLEAN_CSV_FORMAT
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null')
    ENCODING = 'UTF8'
    ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE;

TRUNCATE TABLE FACT_TRANSACTIONS;
TRUNCATE TABLE FACT_LOANS;
TRUNCATE TABLE DIM_ACCOUNT;
TRUNCATE TABLE DIM_CUSTOMER;
TRUNCATE TABLE DIM_BRANCH;
TRUNCATE TABLE DIM_DATE;
TRUNCATE TABLE DIM_LOAN_TYPE;
```

Load dimensions first:

```sql
COPY INTO DIM_DATE
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/dim_date.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO DIM_BRANCH
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/dim_branch.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO DIM_CUSTOMER
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/dim_customer.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO DIM_ACCOUNT
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/dim_account.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO DIM_LOAN_TYPE
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/dim_loan_type.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';
```

Then load facts:

```sql
COPY INTO FACT_LOANS
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/fact_loans.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO FACT_TRANSACTIONS
FROM @BANKING_DW.RAW.BANKING_STAGE/clean/fact_transactions.csv
FILE_FORMAT = (FORMAT_NAME = BANKING_DW.RAW.CLEAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';
```

## 12. Validate the Tables

Run these checks after loading:

```sql
USE DATABASE BANKING_DW;
USE SCHEMA MART;

SELECT 'DIM_DATE' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM DIM_DATE
UNION ALL SELECT 'DIM_BRANCH', COUNT(*) FROM DIM_BRANCH
UNION ALL SELECT 'DIM_CUSTOMER', COUNT(*) FROM DIM_CUSTOMER
UNION ALL SELECT 'DIM_ACCOUNT', COUNT(*) FROM DIM_ACCOUNT
UNION ALL SELECT 'DIM_LOAN_TYPE', COUNT(*) FROM DIM_LOAN_TYPE
UNION ALL SELECT 'FACT_LOANS', COUNT(*) FROM FACT_LOANS
UNION ALL SELECT 'FACT_TRANSACTIONS', COUNT(*) FROM FACT_TRANSACTIONS;

SELECT TRANSACTION_ID, COUNT(*) AS DUPLICATE_COUNT
FROM FACT_TRANSACTIONS
GROUP BY TRANSACTION_ID
HAVING COUNT(*) > 1;

SELECT LOAN_ID, COUNT(*) AS DUPLICATE_COUNT
FROM FACT_LOANS
GROUP BY LOAN_ID
HAVING COUNT(*) > 1;

SELECT TRANSACTION_TYPE, COUNT(*) AS TRANSACTION_COUNT, SUM(AMOUNT) AS TOTAL_AMOUNT
FROM FACT_TRANSACTIONS
GROUP BY TRANSACTION_TYPE
ORDER BY TRANSACTION_TYPE;

SELECT STATUS, COUNT(*) AS LOAN_COUNT, SUM(AMOUNT) AS TOTAL_AMOUNT
FROM FACT_LOANS
GROUP BY STATUS
ORDER BY STATUS;

SELECT
    COUNT_IF(ACCOUNT_ID IS NULL) AS NULL_ACCOUNT_IDS,
    COUNT_IF(DATE_ID IS NULL) AS NULL_DATE_IDS,
    COUNT_IF(BRANCH_ID IS NULL) AS NULL_BRANCH_IDS
FROM FACT_TRANSACTIONS;

SELECT
    COUNT_IF(CUSTOMER_ID IS NULL) AS NULL_CUSTOMER_IDS,
    COUNT_IF(LOAN_TYPE_ID IS NULL) AS NULL_LOAN_TYPE_IDS,
    COUNT_IF(DATE_ID IS NULL) AS NULL_DATE_IDS
FROM FACT_LOANS;

SELECT COUNT(*) AS TRANSACTIONS_WITHOUT_ACCOUNT
FROM FACT_TRANSACTIONS ft
LEFT JOIN DIM_ACCOUNT da ON ft.ACCOUNT_ID = da.ACCOUNT_ID
WHERE da.ACCOUNT_ID IS NULL;

SELECT COUNT(*) AS TRANSACTIONS_WITHOUT_DATE
FROM FACT_TRANSACTIONS ft
LEFT JOIN DIM_DATE dd ON ft.DATE_ID = dd.DATE_ID
WHERE dd.DATE_ID IS NULL;

SELECT COUNT(*) AS TRANSACTIONS_WITHOUT_BRANCH
FROM FACT_TRANSACTIONS ft
LEFT JOIN DIM_BRANCH db ON ft.BRANCH_ID = db.BRANCH_ID
WHERE db.BRANCH_ID IS NULL;

SELECT COUNT(*) AS LOANS_WITHOUT_CUSTOMER
FROM FACT_LOANS fl
LEFT JOIN DIM_CUSTOMER dc ON fl.CUSTOMER_ID = dc.CUSTOMER_ID
WHERE dc.CUSTOMER_ID IS NULL;

SELECT COUNT(*) AS LOANS_WITHOUT_DATE
FROM FACT_LOANS fl
LEFT JOIN DIM_DATE dd ON fl.DATE_ID = dd.DATE_ID
WHERE dd.DATE_ID IS NULL;
```

For a correct load, duplicate queries should return no rows, null counts should be zero, and missing-key queries should return zero.

## 13. Calculate the Loan Default Rate

The current project requirements mention default rate. Run:

```sql
SELECT
    COUNT(*) AS TOTAL_LOANS,
    COUNT_IF(STATUS = 'Defaulted') AS DEFAULTED_LOANS,
    ROUND(
        100.0 * COUNT_IF(STATUS = 'Defaulted') / NULLIF(COUNT(*), 0),
        2
    ) AS DEFAULT_RATE_PERCENT
FROM FACT_LOANS;
```

By branch:

```sql
SELECT
    db.BRANCH_NAME,
    COUNT(*) AS TOTAL_LOANS,
    COUNT_IF(fl.STATUS = 'Defaulted') AS DEFAULTED_LOANS,
    ROUND(
        100.0 * COUNT_IF(fl.STATUS = 'Defaulted') / NULLIF(COUNT(*), 0),
        2
    ) AS DEFAULT_RATE_PERCENT
FROM FACT_LOANS fl
JOIN DIM_BRANCH db ON fl.BRANCH_ID = db.BRANCH_ID
GROUP BY db.BRANCH_NAME
ORDER BY DEFAULT_RATE_PERCENT DESC;
```

## 14. Run the Existing OLAP Queries

1. Open [sql/olap_queries.sql](sql/olap_queries.sql).
2. Select database `BANKING_DW`.
3. Select schema `MART`.
4. Run each query.

The queries use `ROLLUP`, `CUBE`, `CASE`, `ROUND`, `COUNT(DISTINCT ...)`, `LIMIT`, and `NULLS LAST`, which are supported by Snowflake.

The existing Query 10 should be understood as **net cash flow**, not revenue, because it calculates deposits minus withdrawals.

## 15. Connect Power BI

In Power BI Desktop:

1. Select **Get data**.
2. Select **Snowflake**.
3. Enter your Snowflake account identifier.
4. Select warehouse `BANKING_DW_WH`.
5. Select database `BANKING_DW`.
6. Select schema `MART`.
7. Sign in.
8. Import the seven tables.
9. Create these relationships:

```text
DIM_DATE.DATE_ID             -> FACT_TRANSACTIONS.DATE_ID
DIM_DATE.DATE_ID             -> FACT_LOANS.DATE_ID
DIM_BRANCH.BRANCH_ID         -> FACT_TRANSACTIONS.BRANCH_ID
DIM_BRANCH.BRANCH_ID         -> FACT_LOANS.BRANCH_ID
DIM_CUSTOMER.CUSTOMER_ID     -> FACT_LOANS.CUSTOMER_ID
DIM_CUSTOMER.CUSTOMER_ID     -> DIM_ACCOUNT.CUSTOMER_ID
DIM_ACCOUNT.ACCOUNT_ID       -> FACT_TRANSACTIONS.ACCOUNT_ID
DIM_LOAN_TYPE.LOAN_TYPE_ID   -> FACT_LOANS.LOAN_TYPE_ID
```

Start with **Import** mode. It is simpler for this project than DirectQuery.

## 16. Important Existing Project Assumptions

The Snowflake migration does not fix these existing business rules:

- All loans are assigned `loan_type_id = 2`.
- All loans are assigned an interest rate of `12.0`.
- Only `OWNER` account relationships are used.
- Loan account IDs are not retained in `FACT_LOANS`.
- The current age calculation uses the year `1999`.
- Query 4 filters the region to `South`.

These assumptions are defined in [scripts/etl_pipeline.py](scripts/etl_pipeline.py). Review them before presenting the results as real banking business metrics.

## 17. Optional Python Snowflake Loader

The manual SQL process above is useful for learning and testing. For repeatable loading, add this function to a separate Python module such as `scripts/snowflake_loader.py`:

```python
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"


def get_snowflake_connection():
    connection_args = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "BANKING_DW_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "BANKING_DW"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "MART"),
        "role": os.environ["SNOWFLAKE_ROLE"],
    }

    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    if authenticator:
        connection_args["authenticator"] = authenticator
    else:
        connection_args["password"] = os.environ["SNOWFLAKE_PASSWORD"]

    return snowflake.connector.connect(**connection_args)


def quote_sql_string(value: str) -> str:
    """Escape a value before placing it in a SQL string literal."""
    return value.replace("'", "''")


def upload_and_copy_clean_files():
    stage_name = os.getenv(
        "SNOWFLAKE_STAGE",
        "BANKING_DW.RAW.BANKING_STAGE",
    )
    stage_folder = os.getenv("SNOWFLAKE_STAGE_FOLDER", "clean")
    stage_path = f"@{stage_name}/{stage_folder}"

    table_names = [
        "DIM_DATE",
        "DIM_BRANCH",
        "DIM_CUSTOMER",
        "DIM_ACCOUNT",
        "DIM_LOAN_TYPE",
        "FACT_LOANS",
        "FACT_TRANSACTIONS",
    ]

    connection = get_snowflake_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("USE DATABASE BANKING_DW")
        cursor.execute("USE SCHEMA MART")

        # Upload each clean CSV from the local machine to the Snowflake stage.
        for table_name in table_names:
            local_file = CLEAN_DIR / f"{table_name.lower()}.csv"
            if not local_file.exists():
                raise FileNotFoundError(f"Missing clean file: {local_file}")

            escaped_file = quote_sql_string(str(local_file))
            cursor.execute(
                f"PUT 'file://{escaped_file}' "
                f"{stage_path} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
            )

        # Facts must be cleared before dimensions because of relationships.
        for table_name in [
            "FACT_TRANSACTIONS",
            "FACT_LOANS",
            "DIM_ACCOUNT",
            "DIM_CUSTOMER",
            "DIM_BRANCH",
            "DIM_DATE",
            "DIM_LOAN_TYPE",
        ]:
            cursor.execute(f"TRUNCATE TABLE {table_name}")

        # Dimensions must be loaded before facts.
        for table_name in table_names:
            cursor.execute(
                f"COPY INTO {table_name} "
                f"FROM {stage_path}/{table_name.lower()}.csv "
                "FILE_FORMAT = (FORMAT_NAME = 'BANKING_DW.RAW.CLEAN_CSV_FORMAT') "
                "ON_ERROR = 'ABORT_STATEMENT'"
            )

        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    upload_and_copy_clean_files()
    print("Snowflake MART load completed")
```

Install the connector and run it from the repository root:

```powershell
pip install snowflake-connector-python python-dotenv
python scripts/snowflake_loader.py
```

Run the loader only after the MART tables and `CLEAN_CSV_FORMAT` exist.

## 18. Daily Beginner Workflow

After the first successful setup, the repeatable workflow is:

```powershell
Set-Location 'E:\Personal Projects\banking-dw'
.\venv\Scripts\Activate.ps1

pytest -q tests/test_etl_pipeline.py

python -c "from scripts.etl_pipeline import extract_data, transform_dimensions, transform_facts; import os; raw=extract_data('data'); dims=transform_dimensions(raw); facts=transform_facts(raw, dims); os.makedirs('data/clean', exist_ok=True); [value.to_csv('data/clean/' + name + '.csv', index=False) for name, value in {**dims, **facts}.items()]; print('Clean files created')"

python scripts/snowflake_loader.py
```

Then run the validation SQL and OLAP queries in Snowsight.

## 19. Troubleshooting

### `Object does not exist`

Check the worksheet context:

```sql
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
```

Then explicitly run:

```sql
USE WAREHOUSE BANKING_DW_WH;
USE DATABASE BANKING_DW;
USE SCHEMA MART;
```

### `Insufficient privileges`

Your role cannot create or use the requested object. Temporarily use the setup role that created the warehouse, or ask the Snowflake administrator for grants.

### `Number of columns does not match`

The source CSV header does not match the RAW table. Inspect the file header and run:

```sql
DESC TABLE BANKING_DW.RAW.RAW_TRANS;
```

Then add or remove RAW columns to match the source file.

### `PUT` cannot find a file

Use an absolute Windows path in Python or confirm that the terminal is at the repository root. The loader uses the script location, so it should work from any directory.

### The warehouse is suspended

This is expected. `AUTO_RESUME = TRUE` starts it when a query runs, and `AUTO_SUSPEND = 60` stops it after 60 seconds of inactivity.

### The same file is not loading again

Snowflake records previously loaded files. The Python loader uses `OVERWRITE=TRUE` for the upload, but if necessary use a new stage folder such as `clean_2026_09_03/` and update `SNOWFLAKE_STAGE_FOLDER`.

## 20. Completion Checklist

- [ ] `BANKING_DW_WH` exists.
- [ ] `BANKING_DW.RAW`, `STAGING`, and `MART` exist.
- [ ] Six raw files are visible in the stage.
- [ ] Six RAW tables load without errors.
- [ ] Seven clean CSV files are generated.
- [ ] Seven MART tables exist.
- [ ] Dimensions load before facts.
- [ ] Row counts match the clean CSV files.
- [ ] Duplicate-key checks return no rows.
- [ ] Missing foreign-key checks return zero.
- [ ] All OLAP queries run successfully.
- [ ] The default-rate query returns a result.
- [ ] Power BI can connect to `BANKING_DW.MART`.
