"""Measure how feature groups contribute to loan-default prediction."""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "loan_features.csv"
OUTPUT_PATH = ROOT / "outputs" / "feature_group_comparison.csv"

BEHAVIOR = [
    "n_txn", "n_deposit", "n_withdrawal", "sum_deposit", "sum_withdrawal",
    "avg_amount", "std_amount", "avg_balance", "min_balance", "max_balance",
    "balance_at_loan", "months_active", "txn_per_month",
]
LOAN_TERMS = ["amount", "duration", "payments"]
DEMOGRAPHICS = ["age", "gender_bin"]


def main() -> None:
    frame = pd.read_csv(DATA_PATH)
    groups = {
        "behavior_only": BEHAVIOR,
        "behavior_plus_loan_terms": BEHAVIOR + LOAN_TERMS,
        "behavior_plus_loan_terms_demographics": BEHAVIOR + LOAN_TERMS + DEMOGRAPHICS,
    }
    splitter = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
    rows = []
    for name, columns in groups.items():
        estimator = make_pipeline(
            StandardScaler(),
            GradientBoostingClassifier(random_state=42),
        )
        scores = cross_validate(
            estimator,
            frame[columns],
            frame["target"],
            cv=splitter,
            scoring=("f1", "average_precision", "roc_auc"),
        )
        rows.append({
            "feature_group": name,
            "feature_count": len(columns),
            "f1_mean": scores["test_f1"].mean(),
            "f1_std": scores["test_f1"].std(),
            "average_precision_mean": scores["test_average_precision"].mean(),
            "roc_auc_mean": scores["test_roc_auc"].mean(),
        })

    result = pd.DataFrame(rows).round(4)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()