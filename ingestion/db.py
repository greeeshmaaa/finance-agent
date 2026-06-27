import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Date, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    # Plaid's unique transaction id — natural primary key, lets us upsert safely
    transaction_id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)          # merchant / description
    merchant_name = Column(String, nullable=True)  # Plaid's cleaned merchant name (often null)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    ingested_at = Column(DateTime, server_default=func.now())


def init_db():
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(engine)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True)         # deterministic: merchant+type
    merchant = Column(String, nullable=False)
    opportunity_type = Column(String, nullable=False)  # price_creep | recurring_subscription
    current_price = Column(Float, nullable=False)
    prior_price = Column(Float, nullable=True)     # null for plain subscriptions
    pct_change = Column(Float, nullable=True)
    monthly_amount = Column(Float, nullable=False)
    est_annual_savings = Column(Float, nullable=False)
    status = Column(String, server_default="detected")  # detected -> ... (agent updates later)
    detected_at = Column(DateTime, server_default=func.now())
