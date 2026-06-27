"""
Recurring-payment detection via feature engineering + DBSCAN clustering.

Pipeline:
  1. Group transactions by merchant.
  2. Extract rhythm features (cadence, regularity, amount stability).
  3. Cluster with DBSCAN to find the dense group of regular monthly payers;
     irregular merchants fall out as noise.

ML signal: unsupervised clustering on engineered time-series features.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

from ingestion.db import SessionLocal, Transaction


def load_transactions():
    session = SessionLocal()
    try:
        rows = session.query(Transaction).all()
        data = [{"name": r.name, "date": r.date, "amount": r.amount,
                 "category": r.category} for r in rows]
    finally:
        session.close()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def extract_features(df):
    """One feature row per merchant describing its transaction rhythm."""
    rows = []
    for name, group in df.groupby("name"):
        group = group.sort_values("date")
        dates = group["date"].values
        amounts = group["amount"].values
        txn_count = len(group)

        if txn_count >= 2:
            intervals = np.diff(dates).astype("timedelta64[D]").astype(int)
            median_interval = float(np.median(intervals))
            interval_std = float(np.std(intervals))
        else:
            median_interval = 0.0
            interval_std = 0.0

        mean_amount = float(np.mean(amounts))
        std_amount = float(np.std(amounts))
        amount_cv = (std_amount / abs(mean_amount)) if mean_amount != 0 else 0.0

        rows.append({
            "name": name,
            "txn_count": txn_count,
            "median_interval": median_interval,
            "interval_std": interval_std,
            "amount_cv": amount_cv,
            "mean_amount": mean_amount,
        })
    return pd.DataFrame(rows)


def detect_recurring(features):
    """
    Use DBSCAN to find the cluster of regular monthly payers.

    Strategy: cluster merchants that have enough history on their rhythm
    features. The largest/densest cluster represents the regular monthly
    subscriptions. We then confirm with a monthly-cadence sanity check.
    Returns the features frame with an added boolean `is_recurring` column.
    """
    features = features.copy()
    features["is_recurring"] = False

    candidates = features[features["txn_count"] >= 3].copy()
    if len(candidates) < 2:
        return features

    X = candidates[["median_interval", "interval_std", "amount_cv"]].values
    X_scaled = StandardScaler().fit_transform(X)

    cluster_labels = DBSCAN(eps=1.0, min_samples=2).fit_predict(X_scaled)
    candidates = candidates.assign(cluster=cluster_labels)

    # Mark recurring: any merchant placed in a real cluster (label != -1)
    # whose typical cadence is roughly monthly. Using .loc by name avoids
    # any index/column collision on merge.
    for _, row in candidates.iterrows():
        is_monthly = 25 <= row["median_interval"] <= 35
        in_cluster = row["cluster"] != -1
        if in_cluster and is_monthly:
            features.loc[features["name"] == row["name"], "is_recurring"] = True

    return features


def main():
    df = load_transactions()
    features = extract_features(df)
    result = detect_recurring(features)

    recurring = result[result["is_recurring"]].sort_values("mean_amount", ascending=False)
    not_recurring = result[~result["is_recurring"]].sort_values("txn_count", ascending=False)

    print("=== RECURRING PAYMENTS DETECTED ===")
    for _, row in recurring.iterrows():
        kind = "INCOME" if row["mean_amount"] < 0 else "EXPENSE"
        print(f"  {row['name']:<24} ${row['mean_amount']:>9.2f}  "
              f"every ~{row['median_interval']:.0f}d  [{kind}]")

    print("\n=== NOT RECURRING (one-offs / noise) ===")
    for _, row in not_recurring.iterrows():
        print(f"  {row['name']:<24} ${row['mean_amount']:>9.2f}  "
              f"({row['txn_count']} txn)")


if __name__ == "__main__":
    main()
