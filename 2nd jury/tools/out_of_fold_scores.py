"""Regenerate outputs/model_scores.csv with out-of-fold default probabilities.

The modelling notebook scores every loan with a model fitted on all 682 loans, so
its probabilities are in-sample and sharper than anything the model would produce
on a loan it had not seen. This script re-scores with stratified 5-fold
cross_val_predict, where each loan is predicted by a model that never trained on it.
"""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent

DROP = [
    "loan_id", "account_id", "client_id", "district_id",
    "status", "date", "parsed_date", "gender", "target",
]

# Hyperparameters selected by RandomizedSearchCV in notebook 04
# (GradientBoosting baseline tuned, inner F1 0.582).
TUNED = dict(
    subsample=0.7, n_estimators=300, max_depth=1, learning_rate=0.05, random_state=42
)


def main() -> None:
    features = pd.read_csv(ROOT / "data" / "loan_features.csv")
    X = features.drop(columns=DROP)
    y = features["target"]

    pipe = make_pipeline(StandardScaler(), GradientBoostingClassifier(**TUNED))
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    proba = cross_val_predict(pipe, X, y, cv=folds, method="predict_proba")[:, 1]

    scores = features[["loan_id", "account_id"]].copy()
    scores["prob_default"] = proba
    scores["target"] = y.values
    scores.to_csv(ROOT / "outputs" / "model_scores.csv", index=False)

    in_sample = pd.read_csv(ROOT / "outputs" / "_backup_insample" / "model_scores.csv")["prob_default"]
    assert len(scores) == 682, len(scores)
    assert scores["prob_default"].between(0, 1).all()
    print(f"wrote {len(scores)} rows")
    print(f"mean prob   in-sample {in_sample.mean():.3f}  ->  out-of-fold {proba.mean():.3f}")
    print(f"share above 0.50  in-sample {(in_sample > 0.5).mean():.3f}  ->  out-of-fold {(proba > 0.5).mean():.3f}")
    print(f"actual default rate {y.mean():.3f}")


if __name__ == "__main__":
    main()