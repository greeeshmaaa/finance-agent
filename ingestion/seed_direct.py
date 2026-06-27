"""
Load the custom seed dataset directly into Postgres.
Used when Plaid sandbox async backfill doesn't deliver full history.
Produces the same table shape as the Plaid sync path.
"""
import hashlib
from datetime import date

from ingestion.db import SessionLocal, Transaction, init_db
from ingestion.custom_seed import transactions as seed_txns


# Map merchant names to a plausible category (mirrors Plaid's primary categories)
CATEGORY_MAP = {
    "Netflix": "ENTERTAINMENT",
    "Spotify": "ENTERTAINMENT",
    "Hulu Disney Bundle": "ENTERTAINMENT",
    "Planet Fitness": "PERSONAL_CARE",
    "Geico Auto Insurance": "INSURANCE",
    "GUSTO PAY Salary": "INCOME",
    "Amazon Purchase": "GENERAL_MERCHANDISE",
    "Shell Gas Station": "TRANSPORTATION",
    "Whole Foods Market": "FOOD_AND_DRINK",
    "United Airlines": "TRAVEL",
    "Best Buy": "GENERAL_MERCHANDISE",
}


def make_txn_id(name, date_str, amount):
    """Deterministic unique id so re-running upserts instead of duplicating."""
    raw = f"{name}|{date_str}|{amount}"
    return "seed-" + hashlib.md5(raw.encode()).hexdigest()[:20]


def main():
    init_db()
    session = SessionLocal()
    count = 0
    try:
        for t in seed_txns:
            name = t["description"]
            date_str = t["date_posted"]
            amount = t["amount"]
            row = Transaction(
                transaction_id=make_txn_id(name, date_str, amount),
                account_id="seed-checking-account",
                date=date.fromisoformat(date_str),
                name=name,
                merchant_name=name,
                amount=amount,
                category=CATEGORY_MAP.get(name, "OTHER"),
            )
            session.merge(row)
            count += 1
        session.commit()
    finally:
        session.close()
    print(f"Seeded {count} transactions directly into the database.")


if __name__ == "__main__":
    main()
