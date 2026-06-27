"""
Shared state for the negotiation agent's LangGraph workflow.

The state flows through every node; each node reads what it needs and
returns updates that get merged in.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    # The opportunity being worked (loaded from the DB)
    opportunity_id: str
    merchant: str
    opportunity_type: str          # price_creep | recurring_subscription
    current_price: float
    prior_price: Optional[float]
    pct_change: Optional[float]
    est_annual_savings: float

    # Filled by the research node
    market_research: str

    # Filled by the drafting node
    draft_message: str
    message_kind: str              # negotiation | cancellation

    # Filled by the human-in-the-loop step
    approval_status: str           # approved | rejected | edited
    final_message: str
