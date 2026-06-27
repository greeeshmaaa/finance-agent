"""
Drafting node: produce a negotiation or cancellation message based on the
opportunity type, grounded in the detected numbers and market research.

Template-based for now; the build_message() function is the single seam to
swap in a live LLM call later (replace its body with an API call that takes
the same inputs).
"""
from agent.state import AgentState


def build_negotiation_message(merchant, current, prior, pct, research):
    """Price-creep case: ask for the increase to be rolled back."""
    increase = current - prior
    return f"""Subject: Request to Review Recent Price Increase - {merchant}

Hello,

I've been a loyal {merchant} customer and recently noticed my monthly charge
increased from ${prior:.2f} to ${current:.2f} — an increase of ${increase:.2f}
per month (roughly {pct*100:.0f}%).

I'd like to request that my rate be returned to the previous ${prior:.2f}, or
that you offer a comparable retention discount. Based on current market options,
competing services are available at lower price points, and I'd prefer to stay
with {merchant} if we can find a fair rate.

Could you let me know what options are available to bring my cost back in line?

Thank you for your time.

Best regards,
[Your name]"""


def build_cancellation_message(merchant, current, annual, research):
    """Plain subscription case: request cancellation (or a retention offer)."""
    return f"""Subject: Cancellation Request - {merchant}

Hello,

I'd like to cancel my {merchant} subscription, currently billed at
${current:.2f} per month (${annual:.2f} per year).

I've been reviewing my recurring expenses and am reconsidering this
subscription. If there are retention offers or a lower-tier plan available,
I'm open to hearing them; otherwise, please proceed with cancelling my
account and confirm the effective date.

Thank you for your help.

Best regards,
[Your name]"""


def draft_message(state: AgentState) -> dict:
    """Choose the message type based on the opportunity, then build it."""
    merchant = state["merchant"]
    opp_type = state["opportunity_type"]
    current = state["current_price"]
    research = state.get("market_research", "")

    if opp_type == "price_creep":
        message = build_negotiation_message(
            merchant, current, state["prior_price"], state["pct_change"], research
        )
        kind = "negotiation"
    else:
        message = build_cancellation_message(
            merchant, current, state["est_annual_savings"], research
        )
        kind = "cancellation"

    print(f"  [draft] Wrote a {kind} message for {merchant}")
    return {"draft_message": message, "message_kind": kind}


if __name__ == "__main__":
    # Test both message types with fake opportunities
    creep = {
        "merchant": "Planet Fitness", "opportunity_type": "price_creep",
        "current_price": 44.99, "prior_price": 29.99, "pct_change": 0.50,
        "est_annual_savings": 180.0, "market_research": "Competitors at $10-15/mo.",
    }
    sub = {
        "merchant": "Netflix", "opportunity_type": "recurring_subscription",
        "current_price": 15.49, "prior_price": None, "pct_change": None,
        "est_annual_savings": 185.88, "market_research": "",
    }
    print("=" * 60)
    print(draft_message(creep)["draft_message"])
    print("=" * 60)
    print(draft_message(sub)["draft_message"])
