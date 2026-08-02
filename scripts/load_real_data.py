import os
import pandas as pd
from datetime import datetime
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Load environment variables
load_dotenv()

# --- HELPER FUNCTIONS ---
def age_group(age: int) -> str:
    if age <= 25: return "18-25"
    if age <= 35: return "26-35"
    if age <= 50: return "36-50"
    if age <= 65: return "51-65"
    return "65+"

def parse_pkdd_date(date_int):
    # PKDD dates are usually in format YYMMDD
    # e.g., 930101 -> 1993-01-01
    date_str = str(date_int).zfill(6)
    year = int(date_str[0:2])
    # Assume 1900s since this is a 1999 dataset
    year += 1900
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    return pd.to_datetime(f"{year}-{month:02d}-{day:02d}", errors='coerce')

def parse_pkdd_birth_number(birth_number_int):
    # Format: YYMMDD where women have +50 added to month
    # E.g., 705101 -> Female born 1970-01-01
    bn_str = str(birth_number_int).zfill(6)
    year = int(bn_str[0:2]) + 1900
    month = int(bn_str[2:4])
    day = int(bn_str[4:6])
    
    gender = "Female" if month > 50 else "Male"
    month = month - 50 if month > 50 else month
    
    try:
        birth_date = pd.to_datetime(f"{year}-{month:02d}-{day:02d}")
    except:
        birth_date = pd.to_datetime("1970-01-01") # Fallback
        
    # Calculate age as of 1999 (when dataset was released)
    age = 1999 - year
    return pd.Series([birth_date, gender, age])

def get_engine():
    conn_str = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(conn_str)

def main():
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Error: Directory '{data_dir}' not found. Please extract the Kaggle dataset into a folder named '{data_dir}'.")
        print("You should have: client.asc, account.asc, disp.asc, district.asc, loan.asc, trans.asc")
        return

    print("Loading raw CSV files...")
    try:
        df_client = pd.read_csv(f"{data_dir}/client.asc", sep=";")
        df_account = pd.read_csv(f"{data_dir}/account.asc", sep=";")
        df_disp = pd.read_csv(f"{data_dir}/disp.asc", sep=";")
        df_district = pd.read_csv(f"{data_dir}/district.asc", sep=";")
        df_loan = pd.read_csv(f"{data_dir}/loan.asc", sep=";")
        df_trans = pd.read_csv(f"{data_dir}/trans.asc", sep=";", low_memory=False)
    except FileNotFoundError:
        try:
            # Fallback if they are standard commas instead of semicolon .asc files
            df_client = pd.read_csv(f"{data_dir}/client.csv", sep=";")
            df_account = pd.read_csv(f"{data_dir}/account.csv", sep=";")
            df_disp = pd.read_csv(f"{data_dir}/disp.csv", sep=";")
            df_district = pd.read_csv(f"{data_dir}/district.csv", sep=";")
            df_loan = pd.read_csv(f"{data_dir}/loan.csv", sep=";")
            df_trans = pd.read_csv(f"{data_dir}/trans.csv", sep=";", low_memory=False)
            
            # The Kaggle dataset district.csv often uses A1 instead of district_id
            if "A1" in df_district.columns and "district_id" not in df_district.columns:
                df_district.rename(columns={"A1": "district_id"}, inplace=True)
        except Exception as e:
            print("Could not find the dataset files. Ensure they are named correctly (e.g. client.csv).")
            print(e)
            return

    print("Transforming DIM_BRANCH (district)...")
    dim_branch = pd.DataFrame({
        "branch_id": df_district["district_id"],
        "branch_name": df_district["A2"] + " Branch",
        "city": df_district["A2"],
        "region": df_district["A3"],
        "branch_type": np.where(df_district["A4"] > 100000, "Urban", "Rural") # A4 is population
    })

    print("Transforming DIM_CUSTOMER (client)...")
    # Parse birth_number for age/gender
    df_client[['birth_date', 'gender', 'age']] = df_client['birth_number'].apply(parse_pkdd_birth_number)
    df_client['age_group'] = df_client['age'].apply(age_group)
    
    # Map district to city
    district_to_city = dict(zip(df_district["district_id"], df_district["A2"]))
    
    dim_customer = pd.DataFrame({
        "customer_id": df_client["client_id"],
        "first_name": "Client", # PKDD data is fully anonymized
        "last_name": df_client["client_id"].astype(str),
        "gender": df_client["gender"],
        "age": df_client["age"],
        "age_group": df_client['age_group'],
        "city": df_client["district_id"].map(district_to_city),
        "home_branch_id": df_client["district_id"],
        "customer_segment": np.where(df_client["age"] > 50, "Premium", "Regular"), # Mock segment logic
        "account_open_date": pd.to_datetime("1993-01-01") # Fallback, real dates come from account
    })

    print("Transforming DIM_ACCOUNT (account + disp)...")
    # Disp connects client to account. We only want 'OWNER' type for the primary customer_id
    df_owners = df_disp[df_disp["type"] == "OWNER"]
    df_acc_full = pd.merge(df_account, df_owners, on="account_id")
    
    df_acc_full["open_date"] = df_acc_full["date"].apply(parse_pkdd_date)
    
    dim_account = pd.DataFrame({
        "account_id": df_acc_full["account_id"],
        "customer_id": df_acc_full["client_id"],
        "account_type": df_acc_full["frequency"].map({
            "POPLATEK MESICNE": "Savings",
            "POPLATEK TYDNE": "Current", 
            "POPLATEK PO OBRATU": "Fixed Deposit"
        }).fillna("Savings"),
        "open_date": df_acc_full["open_date"],
        "status": "Active" # PKDD accounts are active
    })
    
    # Update dim_customer account_open_date based on earliest account opened
    min_dates = dim_account.groupby("customer_id")["open_date"].min()
    dim_customer["account_open_date"] = dim_customer["customer_id"].map(min_dates).fillna(pd.to_datetime("1993-01-01"))

    print("Preparing DIM_DATE...")
    # Get range of dates from transactions and loans
    all_dates = pd.concat([df_trans["date"].apply(parse_pkdd_date), df_loan["date"].apply(parse_pkdd_date)])
    min_date = all_dates.min()
    max_date = all_dates.max()
    
    # Generate full date range
    date_range = pd.date_range(start=min_date, end=max_date)
    dim_date = pd.DataFrame({
        "date_id": date_range.strftime("%Y%m%d").astype(int),
        "full_date": date_range,
        "day": date_range.day,
        "month": date_range.month,
        "month_name": date_range.strftime("%B"),
        "quarter": date_range.quarter,
        "year": date_range.year,
        "day_of_week": date_range.strftime("%A"),
        "is_weekend": date_range.weekday >= 5
    })

    print("Transforming DIM_LOAN_TYPE...")
    # PKDD has generic loans, we will mock up a few types mapped to the 'purpose' if it existed,
    # but PKDD just has A,B,C,D status. We'll assign a default 'Personal' loan type (ID 2).
    dim_loan_type = pd.DataFrame([
        (1, "Home", 8.5),
        (2, "Personal", 12.0),
        (3, "Auto", 9.5),
        (4, "Education", 7.5),
    ], columns=["loan_type_id", "loan_type_name", "typical_rate_pct"])

    print("Transforming FACT_LOANS...")
    # PKDD status: A=finished good, B=finished bad, C=running good, D=running bad
    status_map = {"A": "Closed", "B": "Defaulted", "C": "Active", "D": "Defaulted"}
    
    # Map account to branch and customer
    acc_to_branch = dict(zip(df_account["account_id"], df_account["district_id"]))
    acc_to_cust = dict(zip(dim_account["account_id"], dim_account["customer_id"]))
    
    df_loan["parsed_date"] = df_loan["date"].apply(parse_pkdd_date)
    
    fact_loans = pd.DataFrame({
        "loan_id": df_loan["loan_id"],
        "customer_id": df_loan["account_id"].map(acc_to_cust),
        "branch_id": df_loan["account_id"].map(acc_to_branch),
        "loan_type_id": 2, # All Personal loans
        "date_id": df_loan["parsed_date"].dt.strftime("%Y%m%d").astype(int),
        "amount": df_loan["amount"],
        "interest_rate": 12.0,
        "tenure_months": df_loan["duration"],
        "status": df_loan["status"].map(status_map)
    }).dropna() # Drop if any customer missing

    print("Transforming FACT_TRANSACTIONS...")
    df_trans["parsed_date"] = df_trans["date"].apply(parse_pkdd_date)
    
    # Transaction type map: PRIJEM (credit) -> Deposit, VYDAJ/VYBER (debit) -> Withdrawal
    type_map = {"PRIJEM": "Deposit", "VYDAJ": "Withdrawal", "VYBER": "Withdrawal"}
    
    fact_transactions = pd.DataFrame({
        "transaction_id": df_trans["trans_id"],
        "account_id": df_trans["account_id"],
        "date_id": df_trans["parsed_date"].dt.strftime("%Y%m%d").astype(int),
        "branch_id": df_trans["account_id"].map(acc_to_branch),
        "transaction_type": df_trans["type"].map(type_map).fillna("Transfer"),
        "amount": df_trans["amount"]
    })

    print(f"  dim_date:          {len(dim_date):>6} rows")
    print(f"  dim_branch:        {len(dim_branch):>6} rows")
    print(f"  dim_customer:      {len(dim_customer):>6} rows")
    print(f"  dim_account:       {len(dim_account):>6} rows")
    print(f"  dim_loan_type:     {len(dim_loan_type):>6} rows")
    print(f"  fact_loans:        {len(fact_loans):>6} rows")
    print(f"  fact_transactions: {len(fact_transactions):>6} rows")

    print("\nLoading into Postgres (banking_dw)...")
    engine = get_engine()
    
    # Clear existing data first
    with engine.begin() as conn:
        print("Clearing old synthetic data...")
        conn.execute(text("TRUNCATE TABLE fact_transactions, fact_loans, dim_account, dim_customer, dim_branch, dim_date, dim_loan_type CASCADE;"))
    
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    dim_branch.to_sql("dim_branch", engine, if_exists="append", index=False)
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    dim_account.to_sql("dim_account", engine, if_exists="append", index=False)
    dim_loan_type.to_sql("dim_loan_type", engine, if_exists="append", index=False)
    fact_loans.to_sql("fact_loans", engine, if_exists="append", index=False)
    
    # Transactions table can be huge (1M+ rows), chunk it
    print("Loading transactions (this may take a minute)...")
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False, chunksize=50000)

    print("Done. Real historical data loaded successfully.")

if __name__ == "__main__":
    main()
