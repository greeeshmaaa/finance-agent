"""
The negotiation agent's LangGraph workflow, with a human-in-the-loop interrupt.

Flow:
  load_opportunity -> research -> draft -> [INTERRUPT for approval] -> finalize

The graph SUSPENDS at the interrupt and will not finalize until a human
resumes it with an explicit decision. The agent never sends messages itself.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from agent.state import AgentState
from agent.nodes import load_opportunity, finalize
from agent.research import research_market_rate
from agent.draft import draft_message


def human_approval(state: AgentState) -> dict:
    """
    Pause for human review. interrupt() suspends the graph and surfaces the
    draft to the caller; execution resumes only when the caller provides a
    decision via Command(resume=...).
    """
    decision = interrupt({
        "merchant": state["merchant"],
        "message_kind": state["message_kind"],
        "draft_message": state["draft_message"],
        "est_annual_savings": state["est_annual_savings"],
    })
    # `decision` is whatever the human passes on resume:
    #   {"approval_status": "approved"} or "rejected", optionally "final_message"
    return {
        "approval_status": decision.get("approval_status", "rejected"),
        "final_message": decision.get("final_message", state["draft_message"]),
    }


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("load_opportunity", load_opportunity)
    g.add_node("research", research_market_rate)
    g.add_node("draft", draft_message)
    g.add_node("human_approval", human_approval)
    g.add_node("finalize", finalize)

    g.add_edge(START, "load_opportunity")
    g.add_edge("load_opportunity", "research")
    g.add_edge("research", "draft")
    g.add_edge("draft", "human_approval")
    g.add_edge("human_approval", "finalize")
    g.add_edge("finalize", END)

    # A checkpointer is required for interrupts to work (it saves the paused state)
    return g.compile(checkpointer=MemorySaver())
