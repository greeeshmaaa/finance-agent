import os
import time
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import Configuration, ApiClient
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from ingestion.db import SessionLocal, Transaction, init_db

load_dotenv()

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": os.environ["PLAID_SECRET"],
    },
)
client = plaid_api.PlaidApi(ApiClient(configuration))


def fetch_all_transactions(access_token):
    """Page through /transactions/sync from an empty cursor until has_more is False."""
    added = []
    cursor = ""
    while True:
        kwargs = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor
        request = TransactionsSyncRequest(**kwargs)
        response = client.transactions_sync(request)
        added.extend(response.added)
        cursor = response.next_cursor
        if not response.has_more:
            break
    return added


def upsert_transactions(transactions):
    session = SessionLocal()
    count = 0
    try:
        for t in transactions:
            category = t.personal_finance_category.primary if t.personal_finance_category else None
            row = Transaction(
                transaction_id=t.transaction_id,
                account_id=t.account_id,
                date=t.date,
                name=t.name,
                merchant_name=t.merchant_name,
                amount=t.amount,
                category=category,
            )
            session.merge(row)
            count += 1
        session.commit()
    finally:
        session.close()
    return count


def main():
    init_db()
    access_token = os.environ["PLAID_ACCESS_TOKEN"]

    # Plaid sandbox populates transaction history asynchronously. Poll several
    # times, keeping the largest batch we see, until the count stabilizes.
    print("Fetching transactions from Plaid sandbox (polling for full history)...")
    best = []
    for attempt in range(10):
        txns = fetch_all_transactions(access_token)
        print(f"  attempt {attempt + 1}: {len(txns)} transactions available")
        if len(txns) > len(best):
            best = txns
        # Stop once we have a substantial history and it stops growing
        if len(txns) >= 60 or (attempt >= 3 and len(txns) == len(best)):
            break
        time.sleep(3)

    if not best:
        print("No transactions returned.")
        return

    count = upsert_transactions(best)
    print(f"Synced {count} transactions into the database.")


if __name__ == "__main__":
    main()
