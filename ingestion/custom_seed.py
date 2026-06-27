"""
Custom sandbox transaction dataset using Plaid's exact custom-user schema.
Contains detectable patterns for Phase 2:
  - Recurring monthly subscriptions (stable cadence)
  - Two subscriptions with mid-history price increases (price creep)
  - Recurring income + irregular one-offs (noise the detector must handle)
"""
import json
from datetime import date, timedelta


def monthly_series(name, amount, months_back, day=15, amount_overrides=None):
    txns = []
    today = date.today()
    for m in range(months_back):
        d = (today.replace(day=1) - timedelta(days=30 * m)).replace(day=day)
        amt = amount
        if amount_overrides and m in amount_overrides:
            amt = amount_overrides[m]
        txns.append({
            "date_transacted": d.isoformat(),
            "date_posted": d.isoformat(),
            "amount": amt,
            "currency": "USD",
            "description": name,
        })
    return txns


transactions = []

# Recurring subscriptions (clean monthly cadence)
transactions += monthly_series("Netflix", 15.49, 12, day=5)
transactions += monthly_series("Spotify", 11.99, 12, day=8)

# Price creep: gym raised price 6 months ago (29.99 -> 44.99)
gym_overrides = {i: 29.99 for i in range(6, 12)}
transactions += monthly_series("Planet Fitness", 44.99, 12, day=2, amount_overrides=gym_overrides)

# Price creep: streaming bundle crept up 3 months ago (19.99 -> 26.99)
bundle_overrides = {i: 19.99 for i in range(3, 12)}
transactions += monthly_series("Hulu Disney Bundle", 26.99, 12, day=12, amount_overrides=bundle_overrides)

# Recurring insurance (monthly, stable)
transactions += monthly_series("Geico Auto Insurance", 142.00, 12, day=20)

# Recurring income as negative-amount transactions (NOT inflow_model — that field
# is only supported on credit/loan accounts, not depository/checking)
transactions += monthly_series("GUSTO PAY Salary", -4200.00, 12, day=1)

# Irregular one-off purchases (noise)
one_offs = [
    ("Amazon Purchase", 63.20, 4),
    ("Shell Gas Station", 41.10, 9),
    ("Whole Foods Market", 88.75, 14),
    ("United Airlines", 312.40, 25),
    ("Best Buy", 229.99, 40),
]
today = date.today()
for name, amt, days_ago in one_offs:
    d = (today - timedelta(days=days_ago)).isoformat()
    transactions.append({
        "date_transacted": d,
        "date_posted": d,
        "amount": amt,
        "currency": "USD",
        "description": name,
    })

override = {
    "override_accounts": [{
        "type": "depository",
        "subtype": "checking",
        "starting_balance": 5000,
        "meta": {"name": "Plaid Checking", "mask": "0000"},
        "transactions": transactions,
    }]
}

if __name__ == "__main__":
    print(json.dumps(override, indent=2))
    print(f"\nTotal transactions: {len(transactions)}")
