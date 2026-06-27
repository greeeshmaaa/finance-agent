"""
Service layer between the Streamlit UI and the agent/database.

Splits the agent's interrupt flow into two callable steps so the UI can:
  1. draft_for_opportunity(): run load -> research -> draft, stop at the pause,
     return the draft for display.
  2. finalize_decision(): resume the paused graph with the human's choice.

Keeps Streamlit code thin and the agent reusable.
"""
import uuid
from langgraph.types import Command

from ingestion.db import SessionLocal, Opportunity
from agent.graph import build_graph

# One compiled graph reused across calls; MemorySaver keeps paused state by thread_id
_graph = build_graph()


def list_opportunities():
    """Return all opportunities as plain dicts, ranked by savings."""
    session = SessionLocal()
    try:
        opps = (session.query(Opportunity)
                .order_by(Opportunity.est_annual_savings.desc())
                .all())
        return [{
            "id": o.id,
            "merchant": o.merchant,
            "opportunity_type": o.opportunity_type,
            "current_price": o.current_price,
            "prior_price": o.prior_price,
            "pct_change": o.pct_change,
            "est_annual_savings": o.est_annual_savings,
            "status": o.status,
        } for o in opps]
    finally:
        session.close()


def draft_for_opportunity(opportunity_id):
    """
    Run the agent up to the human-approval interrupt for a specific opportunity.
    Returns (thread_id, interrupt_data) so the UI can display the draft and
    later resume this exact paused run.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Seed the run with the chosen opportunity so load_opportunity uses it.
    # We pass the id; the graph's load node reads from the DB by highest savings,
    # so for the UI we instead inject the chosen opportunity directly.
    session = SessionLocal()
    try:
        o = session.get(Opportunity, opportunity_id)
        seed = {
            "opportunity_id": o.id,
            "merchant": o.merchant,
            "opportunity_type": o.opportunity_type,
            "current_price": o.current_price,
            "prior_price": o.prior_price,
            "pct_change": o.pct_change,
            "est_annual_savings": o.est_annual_savings,
        }
    finally:
        session.close()

    result = _graph.invoke(seed, config=config)
    interrupt_data = result["__interrupt__"][0].value
    return thread_id, interrupt_data


def finalize_decision(thread_id, approval_status, final_message=None):
    """Resume the paused graph with the human's decision."""
    config = {"configurable": {"thread_id": thread_id}}
    decision = {"approval_status": approval_status}
    if final_message is not None:
        decision["final_message"] = final_message
    final = _graph.invoke(Command(resume=decision), config=config)
    return final
