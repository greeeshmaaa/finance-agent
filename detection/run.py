"""
Detection pipeline: transactions -> ranked opportunities table.

Runs recurring detection + price-creep detection, computes estimated annual
savings, ranks by impact, and upserts into the opportunities table.

Run with: python -m detection.run
"""
import hashlib

from ingestion.db import SessionLocal, Opportunity, init_db
from detection.recurring import load_transactions, extract_features, detect_recurring
from detection.price_creep import find_price_creep


def make_id(merchant, opp_type):
    raw = f"{merchant}|{opp_type}"
    return "opp-" + hashlib.md5(raw.encode()).hexdigest()[:16]


def build_opportunities():
    df = load_transactions()
    features = detect_recurring(extract_features(df))

    # Recurring expenses only (skip income like salary)
    recurring = features[(features["is_recurring"]) & (features["mean_amount"] > 0)]

    opportunities = []
    for _, row in recurring.iterrows():
        merchant = row["name"]
        creep = find_price_creep(df, merchant)

        if creep:
            # Price-creep opportunity: save the difference vs. the old price
            monthly = creep["after_price"]
            annual_savings = (creep["after_price"] - creep["before_price"]) * 12
            opportunities.append({
                "id": make_id(merchant, "price_creep"),
                "merchant": merchant,
                "opportunity_type": "price_creep",
                "current_price": creep["after_price"],
                "prior_price": creep["before_price"],
                "pct_change": creep["pct_change"],
                "monthly_amount": monthly,
                "est_annual_savings": annual_savings,
            })
        else:
            # Plain recurring subscription: potential full cancellation
            monthly = row["mean_amount"]
            opportunities.append({
                "id": make_id(merchant, "recurring_subscription"),
                "merchant": merchant,
                "opportunity_type": "recurring_subscription",
                "current_price": monthly,
                "prior_price": None,
                "pct_change": None,
                "monthly_amount": monthly,
                "est_annual_savings": monthly * 12,
            })

    # Rank by estimated annual savings, highest impact first
    opportunities.sort(key=lambda o: o["est_annual_savings"], reverse=True)
    return opportunities


def persist(opportunities):
    session = SessionLocal()
    try:
        for o in opportunities:
            session.merge(Opportunity(**o))
        session.commit()
    finally:
        session.close()


def main():
    init_db()
    opportunities = build_opportunities()
    persist(opportunities)

    print(f"Detected and saved {len(opportunities)} opportunities (ranked by annual savings):\n")
    print(f"  {'MERCHANT':<24}{'TYPE':<24}{'MONTHLY':>10}{'ANNUAL SAVINGS':>16}")
    print("  " + "-" * 72)
    for o in opportunities:
        print(f"  {o['merchant']:<24}{o['opportunity_type']:<24}"
              f"${o['monthly_amount']:>8.2f}${o['est_annual_savings']:>14.2f}")


if __name__ == "__main__":
    main()
