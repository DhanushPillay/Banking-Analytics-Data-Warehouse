"""Train the advanced models and clusterings that are not in the original notebooks.

Outputs:
  artifacts/metrics/advanced_metrics.csv
  artifacts/rules/cba_rules.csv
  artifacts/models/mlp_classifier.pkl
  artifacts/segments/cluster_labels.csv
  artifacts/segments/cluster_profiles.csv

Run with: venv\\Scripts\\python.exe scripts\\build_advanced_models.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "banking_dw.duckdb"
ARTIFACTS = ROOT / "artifacts"
SEED = 42

DROP = {
    "loan_id",
    "account_id",
    "loan_date_id",
    "client_id",
    "district_id",
    "status",
    "date",
    "parsed_date",
    "gender",
    "target",
}

BIN_SPECS = {
    "amount": ([-np.inf, 50_000, 100_000, np.inf], ["low", "mid", "high"]),
    "duration": ([-np.inf, 12, 24, np.inf], ["short", "mid", "long"]),
    "payments": ([-np.inf, 3_000, 7_000, np.inf], ["low", "mid", "high"]),
    "n_txn": ([-np.inf, 20, 100, np.inf], ["few", "some", "many"]),
    "n_deposit": ([-np.inf, 10, 50, np.inf], ["few", "some", "many"]),
    "n_withdrawal": ([-np.inf, 10, 50, np.inf], ["few", "some", "many"]),
    "avg_balance": ([-np.inf, 0, 20_000, 60_000, np.inf], ["negative", "low", "mid", "high"]),
    "min_balance": ([-np.inf, 0, 10_000, 40_000, np.inf], ["negative", "low", "mid", "high"]),
    "balance_at_loan": ([-np.inf, 0, 20_000, 60_000, np.inf], ["negative", "low", "mid", "high"]),
    "months_active": ([-np.inf, 12, 36, np.inf], ["new", "mid", "old"]),
    "txn_per_month": ([-np.inf, 1, 5, np.inf], ["low", "mid", "high"]),
    "age": ([-np.inf, 30, 45, 60, np.inf], ["young", "mid", "senior", "old"]),
    "gender_bin": ({0: "male", 1: "female"}, None),
}


def load_features() -> pd.DataFrame:
    if DB.exists():
        con = duckdb.connect(str(DB), read_only=True)
        frame = con.execute("SELECT * FROM analytics.loan_features").fetchdf()
        con.close()
        return frame
    return pd.read_csv(ROOT / "data" / "features" / "loan_features.csv")


def scores_at_threshold(y_true: pd.Series, scores: np.ndarray) -> dict:
    best = {"threshold": 0.5, "f1": -1.0}
    for threshold in np.arange(0.05, 0.96, 0.01):
        f1 = f1_score(y_true, scores >= threshold, zero_division=0)
        if f1 > best["f1"]:
            best = {"threshold": float(threshold), "f1": float(f1)}
    threshold = best["threshold"]
    predicted = scores >= threshold
    return {
        "threshold": threshold,
        "accuracy": float((predicted == y_true).mean()),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
    }


def run_mlp(x: pd.DataFrame, y: pd.Series) -> tuple[dict, pd.DataFrame, object]:
    model = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(32, 16),
            alpha=0.001,
            learning_rate_init=0.01,
            max_iter=3000,
            early_stopping=True,
            n_iter_no_change=40,
            random_state=SEED,
        ),
    )
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = cross_val_predict(model, x, y, cv=folds, method="predict_proba")[:, 1]
    metrics = {"model": "MLP", **scores_at_threshold(y, scores)}
    model.fit(x, y)
    return metrics, pd.DataFrame({"prob_default": scores}), model


def binned_items(frame: pd.DataFrame) -> pd.DataFrame:
    """Turn each numeric feature into one interpretable bin per row."""
    cats = pd.DataFrame(index=frame.index)
    for name, (bins, labels) in BIN_SPECS.items():
        cats[name] = pd.cut(frame[name], bins, labels=labels) if labels else frame[name].map(bins)
    return pd.get_dummies(cats, prefix_sep="_").astype(bool)


def mine_default_rules(items: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    basket = items.copy()
    basket["target_default"] = y.eq(1).to_numpy()
    frequent = apriori(basket, min_support=0.03, use_colnames=True, max_len=3)
    if frequent.empty:
        return pd.DataFrame(
            columns=["antecedents", "support", "confidence", "lift", "coverage"]
        )
    rules = association_rules(frequent, metric="confidence", min_threshold=0.5)
    rules = rules[rules["consequents"] == frozenset({"target_default"})].copy()
    if rules.empty:
        return pd.DataFrame(
            columns=["antecedents", "support", "confidence", "lift", "coverage"]
        )
    rules["coverage"] = rules["support"] / rules["confidence"]
    rules["antecedents"] = rules["antecedents"].apply(
        lambda value: ", ".join(sorted(value))
    )
    return rules[["antecedents", "support", "confidence", "lift", "coverage"]].sort_values(
        ["confidence", "lift"], ascending=False
    )


def rule_scores(items: pd.DataFrame, rules: pd.DataFrame) -> np.ndarray:
    scores = np.zeros(len(items), dtype=float)
    for rule in rules.itertuples(index=False):
        columns = rule.antecedents.split(", ")
        mask = items[columns].all(axis=1).to_numpy()
        scores[mask] = np.maximum(scores[mask], rule.confidence)
    return scores


def run_cba(x: pd.DataFrame, y: pd.Series) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = np.zeros(len(y), dtype=float)
    for train_index, test_index in folds.split(x, y):
        train_items = binned_items(x.iloc[train_index])
        test_items = binned_items(x.iloc[test_index])
        rules = mine_default_rules(train_items, y.iloc[train_index])
        if not rules.empty:
            scores[test_index] = rule_scores(test_items, rules)
    metrics = {"model": "CBA rules", **scores_at_threshold(y, scores)}
    final_rules = mine_default_rules(binned_items(x), y)
    return metrics, pd.DataFrame({"prob_default": scores}), final_rules


def k_medoids(distance: np.ndarray, k: int, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    medoids = rng.choice(len(distance), k, replace=False)
    for _ in range(100):
        labels = np.argmin(distance[:, medoids], axis=1)
        updated = []
        for cluster in range(k):
            members = np.where(labels == cluster)[0]
            if len(members) == 0:
                updated.append(int(rng.choice(len(distance))))
                continue
            block = distance[np.ix_(members, members)]
            updated.append(int(members[np.argmin(block.sum(axis=0))]))
        updated = np.array(updated)
        if set(updated) == set(medoids):
            break
        medoids = updated
    return np.argmin(distance[:, medoids], axis=1)


def best_k(scaled: np.ndarray, fit) -> int:
    scores = {k: silhouette_score(scaled, fit(k)) for k in range(2, 6)}
    return max(scores, key=scores.get)


def run_clusters(x: pd.DataFrame, loan_ids: pd.Series, y: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    scaled = StandardScaler().fit_transform(x)
    distance = np.sqrt(((scaled[:, None, :] - scaled[None, :, :]) ** 2).sum(axis=2))
    medoid_k = best_k(scaled, lambda k: k_medoids(distance, k))
    medoid_labels = k_medoids(distance, medoid_k)

    agnes_k = best_k(
        scaled,
        lambda k: AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(scaled),
    )
    agnes = AgglomerativeClustering(n_clusters=agnes_k, linkage="ward").fit_predict(scaled)

    best_dbscan = (-1.0, np.full(len(x), -1))
    for eps in np.arange(0.8, 3.01, 0.1):
        labels = DBSCAN(eps=float(eps), min_samples=5).fit_predict(scaled)
        clusters = set(labels) - {-1}
        if not 2 <= len(clusters) <= 10:
            continue
        silhouette = silhouette_score(scaled, labels)
        if silhouette > best_dbscan[0]:
            best_dbscan = (silhouette, labels)

    labels = pd.DataFrame({"loan_id": loan_ids.to_numpy()})
    labels["kmedoids"] = medoid_labels
    labels["agnes"] = agnes
    labels["dbscan"] = best_dbscan[1]

    profiles = []
    for method in ["kmedoids", "agnes", "dbscan"]:
        for cluster, group in labels.groupby(method):
            profiles.append(
                {
                    "method": method,
                    "cluster": int(cluster),
                    "size": len(group),
                    "default_rate": float(y.iloc[group.index].mean()),
                    "avg_amount": float(x.iloc[group.index]["amount"].mean()),
                    "avg_balance": float(x.iloc[group.index]["avg_balance"].mean()),
                    "avg_age": float(x.iloc[group.index]["age"].mean()),
                    "avg_n_txn": float(x.iloc[group.index]["n_txn"].mean()),
                }
            )
    return labels, pd.DataFrame(profiles)


def main() -> None:
    features = load_features().reset_index(drop=True)
    x = features.drop(columns=[column for column in DROP if column in features])
    y = features["target"]

    print("Training MLP...")
    mlp_metrics, mlp_scores, mlp_model = run_mlp(x, y)

    print("Mining CBA rules...")
    cba_metrics, cba_scores, cba_rules = run_cba(x, y)

    for folder in ("metrics", "models", "rules", "segments"):
        (ARTIFACTS / folder).mkdir(parents=True, exist_ok=True)

    metrics = pd.DataFrame([mlp_metrics, cba_metrics])
    metrics.to_csv(ARTIFACTS / "metrics" / "advanced_metrics.csv", index=False)

    joblib.dump(mlp_model, ARTIFACTS / "models" / "mlp_classifier.pkl")

    cba_rules.to_csv(ARTIFACTS / "rules" / "cba_rules.csv", index=False)

    scored = features[["loan_id"]].copy()
    scored["mlp_prob_default"] = mlp_scores["prob_default"].to_numpy()
    scored["cba_score"] = cba_scores["prob_default"].to_numpy()
    scored["target"] = y.to_numpy()
    scored.to_csv(ARTIFACTS / "metrics" / "advanced_scores.csv", index=False)

    print("Clustering...")
    cluster_x = x.copy()
    labels, profiles = run_clusters(cluster_x, features["loan_id"], y)
    labels.to_csv(ARTIFACTS / "segments" / "cluster_labels.csv", index=False)
    profiles.to_csv(ARTIFACTS / "segments" / "cluster_profiles.csv", index=False)

    print(metrics.to_string(index=False))
    print(f"rules: {len(cba_rules)}")
    print(profiles.to_string(index=False))


if __name__ == "__main__":
    main()
