"""
Research node: find market/competitor pricing context for the opportunity,
so the drafted message can reference real alternatives.
"""
import os
from tavily import TavilyClient

from agent.state import AgentState


def research_market_rate(state: AgentState) -> dict:
    """Search for competitor/market pricing for this merchant's service."""
    merchant = state["merchant"]
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    query = f"{merchant} subscription price competitors cheaper alternatives"
    try:
        resp = client.search(query, max_results=3)
        findings = []
        for r in resp.get("results", []):
            title = r.get("title", "")
            content = r.get("content", "")[:300]
            findings.append(f"- {title}: {content}")
        research = "\n".join(findings) if findings else "No market data found."
    except Exception as e:
        research = f"(Market research unavailable: {e})"

    print(f"  [research] Found market context for {merchant}")
    return {"market_research": research}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_state = {"merchant": "Planet Fitness"}
    result = research_market_rate(test_state)
    print(result["market_research"])
