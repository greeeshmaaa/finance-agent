"""
Database-facing nodes for the agent: load an opportunity to work on, and
finalize the result after human approval.

The agent NEVER sends anything. 'finalize' only records the human's decision
and logs the (approved) message — sending is left to the human.
"""
from ingestion.db import SessionLocal, Opportunity
from agent.state import AgentState


def load_opportunity(state: AgentState) -> dict:
    """Load the highest-savings opportunity still in 'detected' status."""
    session = SessionLocal()
    try:
        opp = (session.query(Opportunity)
               .filter(Opportunity.status == "detected")
               .order_by(Opportunity.est_annual_savings.desc())
               .first())
        if opp is None:
            print("  [load] No pending opportunities.")
            return {}
        print(f"  [load] Working opportunity: {opp.merchant} "
              f"(${opp.est_annual_savings:.2f}/yr potential)")
        return {
            "opportunity_id": opp.id,
            "merchant": opp.merchant,
            "opportunity_type": opp.opportunity_type,
            "current_price": opp.current_price,
            "prior_price": opp.prior_price,
            "pct_change": opp.pct_change,
            "est_annual_savings": opp.est_annual_savings,
        }
    finally:
        session.close()


def finalize(state: AgentState) -> dict:
    """Record the human's decision. Never sends; only updates status."""
    decision = state.get("approval_status", "rejected")
    session = SessionLocal()
    try:
        opp = session.get(Opportunity, state["opportunity_id"])
        if opp:
            # Map the human decision to a terminal status on the opportunity
            opp.status = {
                "approved": "approved_ready_to_send",
                "edited": "approved_ready_to_send",
                "rejected": "dismissed",
            }.get(decision, "dismissed")
            session.commit()
            print(f"  [finalize] {opp.merchant} -> {opp.status}")
    finally:
        session.close()

    final = state.get("final_message", state.get("draft_message", ""))
    return {"final_message": final}
