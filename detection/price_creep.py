"""
Price-creep detection on recurring expenses.

For each recurring merchant, sort its charges by date and find the changepoint
that best splits the series into a cheaper 'before' and pricier 'after'.
If the sustained increase exceeds a threshold, flag it as price creep.

This is a lightweight changepoint detection over each merchant's amount series.
"""
import numpy as np
import pandas as pd

from ingestion.db import SessionLocal, Transaction
from detection.recurring import load_transactions, extract_features, detect_recurring

CREEP_THRESHOLD = 0.10  # 10% sustained increase counts as price creep


def find_price_creep(df, merchant):
    """
    Return creep info for one merchant, or None if no meaningful increase.

    Finds the split point maximizing the jump between the mean of the earlier
    charges and the mean of the later charges.
    """
    series = (df[df["name"] == merchant]
              .sort_values("date")[["date", "amount"]]
              .reset_index(drop=True))
    amounts = series["amount"].values
    n = len(amounts)
    if n < 4:
        return None  # need enough points to find a stable before/after

    best = None
    # Try each split that leaves at least 2 points on each side
    for i in range(2, n - 1):
        before = amounts[:i]
        after = amounts[i:]
        before_mean = before.mean()
        after_mean = after.mean()
        if before_mean <= 0:
            continue
        pct_change = (after_mean - before_mean) / before_mean
        if best is None or pct_change > best["pct_change"]:
            best = {
                "split_index": i,
                "before_price": float(before_mean),
                "after_price": float(after_mean),
                "pct_change": float(pct_change),
                "change_date": series.loc[i, "date"],
            }

    if best and best["pct_change"] >= CREEP_THRESHOLD:
        return best
    return None


def main():
    df = load_transactions()
    features = extract_features(df)
    result = detect_recurring(features)

    # Only check recurring EXPENSES (positive amount); skip income
    recurring_expenses = result[
        (result["is_recurring"]) & (result["mean_amount"] > 0)
    ]["name"].tolist()

    print("=== PRICE CREEP DETECTED ===")
    found_any = False
    for merchant in recurring_expenses:
        creep = find_price_creep(df, merchant)
        if creep:
            found_any = True
            print(f"  {merchant}")
            print(f"      ${creep['before_price']:.2f} -> ${creep['after_price']:.2f}  "
                  f"(+{creep['pct_change']*100:.0f}%)  "
                  f"around {pd.to_datetime(creep['change_date']).date()}")
    if not found_any:
        print("  (none)")

    print("\n=== STABLE RECURRING (no creep) ===")
    for merchant in recurring_expenses:
        if find_price_creep(df, merchant) is None:
            print(f"  {merchant}")


if __name__ == "__main__":
    main()
