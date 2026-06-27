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
