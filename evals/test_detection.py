"""
Evaluation harness for the detection layer.

Because the seed dataset is designed, ground truth is known. We measure
precision and recall of:
  1. recurring-payment detection
  2. price-creep detection

Run with: python -m evals.test_detection
"""
from detection.recurring import load_transactions, extract_features, detect_recurring
from detection.price_creep import find_price_creep

# --- Ground truth (from the designed seed dataset) ---
# Merchants that ARE genuine recurring payments (monthly cadence).
# Note: salary is recurring but income, so it is expected to be detected as
# recurring-by-rhythm; we evaluate expense recurring detection separately below.
TRUE_RECURRING = {
    "Netflix", "Spotify", "Planet Fitness",
    "Hulu Disney Bundle", "Geico Auto Insurance", "GUSTO PAY Salary",
}

# Merchants that genuinely had a price increase.
TRUE_PRICE_CREEP = {"Planet Fitness", "Hulu Disney Bundle"}

# All merchants in the dataset (for computing false positives).
ALL_ONE_OFFS = {
    "Amazon Purchase", "Best Buy", "Shell Gas Station",
    "United Airlines", "Whole Foods Market",
}


def precision_recall(predicted: set, truth: set):
    tp = len(predicted & truth)
    fp = len(predicted - truth)
    fn = len(truth - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


def main():
    df = load_transactions()
    features = detect_recurring(extract_features(df))

    # --- Eval 1: recurring detection ---
    predicted_recurring = set(features[features["is_recurring"]]["name"])
    p, r, f1, tp, fp, fn = precision_recall(predicted_recurring, TRUE_RECURRING)

    print("=" * 56)
    print("EVAL 1 — Recurring-payment detection")
    print("=" * 56)
    print(f"  Predicted recurring: {sorted(predicted_recurring)}")
    print(f"  Ground truth:        {sorted(TRUE_RECURRING)}")
    print(f"  Precision: {p:.2f}   Recall: {r:.2f}   F1: {f1:.2f}")
    print(f"  (TP={tp}, FP={fp}, FN={fn})")

    # --- Eval 2: price-creep detection ---
    recurring_expenses = features[
        (features["is_recurring"]) & (features["mean_amount"] > 0)
    ]["name"].tolist()
    predicted_creep = {m for m in recurring_expenses if find_price_creep(df, m)}
    p2, r2, f12, tp2, fp2, fn2 = precision_recall(predicted_creep, TRUE_PRICE_CREEP)

    print("\n" + "=" * 56)
    print("EVAL 2 — Price-creep detection")
    print("=" * 56)
    print(f"  Predicted creep: {sorted(predicted_creep)}")
    print(f"  Ground truth:    {sorted(TRUE_PRICE_CREEP)}")
    print(f"  Precision: {p2:.2f}   Recall: {r2:.2f}   F1: {f12:.2f}")
    print(f"  (TP={tp2}, FP={fp2}, FN={fn2})")

    # --- Summary ---
    print("\n" + "=" * 56)
    overall = (p == 1.0 and r == 1.0 and p2 == 1.0 and r2 == 1.0)
    print("RESULT:", "All detections correct (100% precision & recall)."
          if overall else "Some detections missed — see above.")
    print("=" * 56)


if __name__ == "__main__":
    main()
