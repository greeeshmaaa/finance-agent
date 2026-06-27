"""
Run the negotiation agent end-to-end with human-in-the-loop approval.

The graph runs until the approval interrupt, then pauses. We surface the draft,
collect the human's decision from the terminal, and resume the graph with it.
The agent never sends anything — the human owns the final action.

Run with: python -m agent.run
"""
import uuid
from dotenv import load_dotenv
from langgraph.types import Command

from agent.graph import build_graph

load_dotenv()


def main():
    graph = build_graph()
    # Each run needs a thread id so the checkpointer can save/restore the pause
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print("Running agent...\n")
    result = graph.invoke({}, config=config)

    # If there are no pending opportunities, load returned empty and we stop
    if "__interrupt__" not in result and "merchant" not in result:
        print("Nothing to do.")
        return

    # The graph is now paused at the interrupt. Pull the surfaced draft.
    interrupt_data = result["__interrupt__"][0].value

    print("\n" + "=" * 64)
    print("HUMAN APPROVAL REQUIRED")
    print("=" * 64)
    print(f"Merchant:        {interrupt_data['merchant']}")
    print(f"Message type:    {interrupt_data['message_kind']}")
    print(f"Annual savings:  ${interrupt_data['est_annual_savings']:.2f}")
    print("-" * 64)
    print(interrupt_data["draft_message"])
    print("=" * 64)

    # Collect the decision
    choice = input("\nApprove this draft? [y]es / [n]o / [e]dit: ").strip().lower()

    if choice == "y":
        decision = {"approval_status": "approved"}
    elif choice == "e":
        print("Enter your edited message. End with a blank line:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        decision = {"approval_status": "edited", "final_message": "\n".join(lines)}
    else:
        decision = {"approval_status": "rejected"}

    # Resume the graph from the pause with the human's decision
    final = graph.invoke(Command(resume=decision), config=config)

    print("\n" + "=" * 64)
    print("RESULT")
    print("=" * 64)
    print(f"Decision: {final.get('approval_status')}")
    if final.get("approval_status") in ("approved", "edited"):
        print("\nFinal message (ready for YOU to send — the agent does not send):\n")
        print(final.get("final_message", ""))
    else:
        print("Opportunity dismissed. No message will be sent.")


if __name__ == "__main__":
    main()
