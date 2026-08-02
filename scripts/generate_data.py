"""
Generates representative synthetic banking data (customers, accounts, branches,
loans, transactions) and loads it into the banking_dw Postgres database
following the star/galaxy schema in sql/schema.sql.

Usage:
    python scripts/generate_data.py
"""

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine

load_dotenv()
fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

# ---------------- CONFIG ----------------
N_BRANCHES = 15
N_CUSTOMERS = 800
N_LOANS = 300
N_TRANSACTIONS = 8000
YEAR = 2025  # 12 months of activity

CITIES_REGIONS = [
    ("Pune", "West"), ("Mumbai", "West"), ("Nagpur", "West"),
    ("Bengaluru", "South"), ("Chennai", "South"), ("Hyderabad", "South"),
    ("Delhi", "North"), ("Jaipur", "North"), ("Lucknow", "North"),
    ("Kolkata", "East"), ("Patna", "East"), ("Bhubaneswar", "East"),
]

ACCOUNT_TYPES = ["Savings", "Current", "Fixed Deposit"]
LOAN_TYPES = [
    (1, "Home", 8.5),
    (2, "Personal", 12.0),
    (3, "Auto", 9.5),
    (4, "Education", 7.5),
]
TXN_TYPES = ["Deposit", "Withdrawal", "Transfer"]


def age_group(age: int) -> str:
    if age <= 25:
        return "18-25"
    if age <= 35:
        return "26-35"
    if age <= 50:
        return "36-50"
    if age <= 65:
        return "51-65"
    return "65+"


def build_dim_date(year: int) -> pd.DataFrame:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    rows = []
    d = start
    while d <= end:
        rows.append({
            "date_id": int(d.strftime("%Y%m%d")),
            "full_date": d,
            "day": d.day,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "quarter": (d.month - 1) // 3 + 1,
            "year": d.year,
            "day_of_week": d.strftime("%A"),
            "is_weekend": d.weekday() >= 5,
        })
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def build_dim_branch(n: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        city, region = random.choice(CITIES_REGIONS)
        rows.append({
            "branch_id": i,
            "branch_name": f"{city} {fake.street_suffix()} Branch",
            "city": city,
            "region": region,
            "branch_type": random.choices(
                ["Urban", "Semi-Urban", "Rural"], weights=[0.5, 0.35, 0.15]
            )[0],
        })
    return pd.DataFrame(rows)


def build_dim_customer(n: int, branch_ids: list, year: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        age = int(np.clip(np.random.normal(38, 13), 18, 80))
        open_date = fake.date_between(start_date=date(year - 5, 1, 1), end_date=date(year, 12, 31))
        city, _ = random.choice(CITIES_REGIONS)
        rows.append({
            "customer_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "gender": random.choice(["Male", "Female"]),
            "age": age,
            "age_group": age_group(age),
            "city": city,
            "home_branch_id": random.choice(branch_ids),
            "customer_segment": random.choices(
                ["Regular", "Premium", "VIP"], weights=[0.7, 0.25, 0.05]
            )[0],
            "account_open_date": open_date,
        })
    return pd.DataFrame(rows)


def build_dim_account(customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    account_id = 1
    for _, cust in customers.iterrows():
        n_accounts = random.choices([1, 2], weights=[0.7, 0.3])[0]
        for _ in range(n_accounts):
            rows.append({
                "account_id": account_id,
                "customer_id": cust["customer_id"],
                "account_type": random.choices(
                    ACCOUNT_TYPES, weights=[0.6, 0.3, 0.1]
                )[0],
                "open_date": cust["account_open_date"],
                "status": random.choices(["Active", "Closed"], weights=[0.9, 0.1])[0],
            })
            account_id += 1
    return pd.DataFrame(rows)


def build_dim_loan_type() -> pd.DataFrame:
    return pd.DataFrame(
        LOAN_TYPES, columns=["loan_type_id", "loan_type_name", "typical_rate_pct"]
    )


def build_fact_loans(n: int, customers: pd.DataFrame, branch_ids: list, dim_date: pd.DataFrame) -> pd.DataFrame:
    rows = []
    date_ids = dim_date["date_id"].tolist()
    cust_ids = customers["customer_id"].tolist()
    for loan_id in range(1, n + 1):
        loan_type_id, _, base_rate = random.choice(LOAN_TYPES)
        rows.append({
            "loan_id": loan_id,
            "customer_id": random.choice(cust_ids),
            "branch_id": random.choice(branch_ids),
            "loan_type_id": loan_type_id,
            "date_id": random.choice(date_ids),
            "amount": round(np.random.uniform(50000, 4000000), 2),
            "interest_rate": round(base_rate + np.random.uniform(-0.5, 0.5), 2),
            "tenure_months": random.choice([12, 24, 36, 60, 120, 240]),
            "status": random.choices(
                ["Active", "Closed", "Defaulted"], weights=[0.65, 0.3, 0.05]
            )[0],
        })
    return pd.DataFrame(rows)


def build_fact_transactions(n: int, accounts: pd.DataFrame, dim_date: pd.DataFrame,
                             customers: pd.DataFrame) -> pd.DataFrame:
    cust_to_branch = dict(zip(customers["customer_id"], customers["home_branch_id"]))
    acct_ids = accounts["account_id"].tolist()
    acct_to_cust = dict(zip(accounts["account_id"], accounts["customer_id"]))
    date_ids = dim_date["date_id"].tolist()

    rows = []
    for txn_id in range(1, n + 1):
        acct_id = random.choice(acct_ids)
        cust_id = acct_to_cust[acct_id]
        txn_type = random.choices(TXN_TYPES, weights=[0.45, 0.4, 0.15])[0]
        amount = round(np.random.lognormal(mean=8.5, sigma=1.0), 2)  # skewed, realistic
        rows.append({
            "transaction_id": txn_id,
            "account_id": acct_id,
            "date_id": random.choice(date_ids),
            "branch_id": cust_to_branch[cust_id],
            "transaction_type": txn_type,
            "amount": amount,
        })
    return pd.DataFrame(rows)


def get_engine():
    conn_str = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(conn_str)


def main():
    print("Generating dimensions...")
    dim_date = build_dim_date(YEAR)
    dim_branch = build_dim_branch(N_BRANCHES)
    dim_customer = build_dim_customer(N_CUSTOMERS, dim_branch["branch_id"].tolist(), YEAR)
    dim_account = build_dim_account(dim_customer)
    dim_loan_type = build_dim_loan_type()

    print("Generating facts...")
    fact_loans = build_fact_loans(N_LOANS, dim_customer, dim_branch["branch_id"].tolist(), dim_date)
    fact_transactions = build_fact_transactions(N_TRANSACTIONS, dim_account, dim_date, dim_customer)

    print(f"  dim_date:          {len(dim_date):>6} rows")
    print(f"  dim_branch:        {len(dim_branch):>6} rows")
    print(f"  dim_customer:      {len(dim_customer):>6} rows")
    print(f"  dim_account:       {len(dim_account):>6} rows")
    print(f"  dim_loan_type:     {len(dim_loan_type):>6} rows")
    print(f"  fact_loans:        {len(fact_loans):>6} rows")
    print(f"  fact_transactions: {len(fact_transactions):>6} rows")

    print("\nLoading into Postgres (banking_dw)...")
    engine = get_engine()
    # Order matters: dimensions before facts (FK constraints)
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    dim_branch.to_sql("dim_branch", engine, if_exists="append", index=False)
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    dim_account.to_sql("dim_account", engine, if_exists="append", index=False)
    dim_loan_type.to_sql("dim_loan_type", engine, if_exists="append", index=False)
    fact_loans.to_sql("fact_loans", engine, if_exists="append", index=False)
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False)

    print("Done. Data loaded successfully.")


if __name__ == "__main__":
    main()
