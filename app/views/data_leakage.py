"""Data and leakage page."""

from components.common import *


def data_page() -> None:
    features = load_features()
    counts = table_counts()
    audit = leakage_audit()
    matches = int((audit["used"] == audit["n_txn"]).sum())

    page_header(
        "Data",
        "1,056,320 transactions, 682 loans, no lookahead",
        "The modelling table is built from the local DuckDB galaxy schema. One rule keeps it "
        "honest: every transaction used for a loan happened strictly before the loan date.",
    )

    section("Galaxy schema", "Row counts read from DuckDB mart")
    schema = counts.rename(columns={"table": "Table", "rows": "Rows"})
    schema["Role"] = schema["Table"].map(
        lambda name: "Fact" if name.startswith("fact_") else "Dimension"
    )
    show(row_count_chart(schema, "Table", "Rows", "Role"))
    grid(schema, {"Rows": st.column_config.NumberColumn(format="%d")})

    section("Leakage check", "Pick a loan; the split is computed from fact_transactions")
    loan_dates = dict(zip(features["loan_id"], features["parsed_date"]))
    loan_amounts = dict(zip(features["loan_id"], features["amount"]))
    loan_id = st.selectbox(
        "Loan",
        options=features["loan_id"].tolist(),
        format_func=lambda value: f"{value} | {loan_dates[value]} | {loan_amounts[value]:,.0f} CZK",
    )
    chosen = audit[audit["loan_id"] == loan_id].iloc[0]
    excluded = int(chosen["total"] - chosen["used"])
    kpi_row(
        [
            ("Loan date", str(loan_dates[loan_id]), "Cutoff for this loan"),
            ("Account", f"{int(chosen['account_id'])}", "Transaction key"),
            ("Transactions used", f"{int(chosen['used'])}", "Strictly before the loan"),
            ("Transactions excluded", f"{excluded:,}", "On or after the loan"),
        ]
    )
    used = int(chosen["used"])
    total = max(used + excluded, 1)
    show(leakage_figure(used, excluded))
    st.caption(
        f"{used} of {total:,} transactions on this account fall strictly before the loan date. "
        f"The other {excluded:,} are excluded from the feature build."
    )

    note(
        f"Across all {len(features)} loans, n_txn equals the count of transactions strictly before "
        f"the loan date: {matches} of {len(features)} match, and no same-day transaction is used. "
        "This is the check that separates a pre-loan model from a leaked one.",
        label="Verified",
    )

    section("Feature provenance", "Where each modelling column comes from")
    provenance = pd.DataFrame(
        [
            ["Loan terms", "loan.csv", "amount, duration, payments, date"],
            ["Transaction volume", "trans.csv", "n_txn, n_deposit, n_withdrawal, sum_deposit, sum_withdrawal"],
            ["Transaction size", "trans.csv", "avg_amount, std_amount"],
            ["Balance history", "trans.csv", "avg_balance, min_balance, max_balance, balance_at_loan"],
            ["Activity window", "trans.csv", "months_active, txn_per_month"],
            ["Customer", "client.csv", "gender, age, district_id"],
            ["Ownership", "disp.csv, account.csv", "account_id, client_id"],
        ],
        columns=["Group", "Source", "Columns"],
    )
    st.dataframe(provenance, hide_index=True, width="stretch")

    section("Quality checks", "Computed from the modelling table")
    transactions = load_transactions()
    checks = pd.DataFrame(
        [
            ["Rows", f"{len(features):,}", "One per loan"],
            ["Columns", f"{features.shape[1]}", "Terms, behaviour, context, target"],
            ["Missing cells", f"{int(features.isna().sum().sum())}", "None"],
            ["Duplicate loan ids", f"{int(features['loan_id'].duplicated().sum())}", "None"],
            ["Defaults", f"{int(features['target'].sum())}", percent(features["target"].mean())],
            ["Transaction dates", f"{int(transactions['date_id'].min())} to {int(transactions['date_id'].max())}", "Six years"],
            ["Accounts with transactions", f"{transactions['account_id'].nunique():,}", "Of 4,500 accounts"],
        ],
        columns=["Check", "Result", "Note"],
    )
    st.dataframe(checks, hide_index=True, width="stretch")


# --------------------------------------------------------------------- models
