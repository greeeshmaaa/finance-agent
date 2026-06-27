"""
Streamlit approval-queue UI for the Personal Finance Negotiation Agent.

Shows detected savings opportunities, runs the agent live (research + draft)
on the one you select, and lets you approve, edit, or reject the draft.
The agent never sends anything — you own the final action.

Run with: streamlit run ui/app.py
"""
import streamlit as st
from dotenv import load_dotenv

from ui.service import list_opportunities, draft_for_opportunity, finalize_decision

load_dotenv()

st.set_page_config(page_title="Finance Negotiation Agent", page_icon="$", layout="wide")

# ---- Status display helpers ----
STATUS_LABELS = {
    "detected": ("Needs review", "gray"),
    "approved_ready_to_send": ("Approved — ready for you to send", "green"),
    "dismissed": ("Dismissed", "red"),
}

TYPE_LABELS = {
    "price_creep": "Price increase",
    "recurring_subscription": "Recurring subscription",
}


def reset_draft_state():
    for k in ("thread_id", "interrupt_data", "active_opp"):
        st.session_state.pop(k, None)


# ---- Header ----
st.title("Finance Negotiation Agent")
st.caption("Detected savings opportunities from your transactions. "
           "Run the agent to draft a message — you approve before anything is sent.")

opportunities = list_opportunities()
total_potential = sum(o["est_annual_savings"] for o in opportunities
                      if o["status"] != "dismissed")
st.metric("Total potential annual savings", f"${total_potential:,.2f}")

st.divider()

left, right = st.columns([1, 1.3], gap="large")

# ---- LEFT: the opportunity queue ----
with left:
    st.subheader("Opportunities")
    for o in opportunities:
        label, color = STATUS_LABELS.get(o["status"], (o["status"], "gray"))
        with st.container(border=True):
            st.markdown(f"**{o['merchant']}**")
            st.markdown(f"{TYPE_LABELS.get(o['opportunity_type'], o['opportunity_type'])} "
                        f"· ${o['current_price']:.2f}/mo")
            st.markdown(f"Potential savings: **${o['est_annual_savings']:,.2f}/yr**")
            st.markdown(f":{color}[{label}]")
            if o["status"] == "detected":
                if st.button("Run agent", key=f"run-{o['id']}"):
                    reset_draft_state()
                    with st.spinner(f"Researching {o['merchant']} and drafting..."):
                        thread_id, interrupt_data = draft_for_opportunity(o["id"])
                    st.session_state.thread_id = thread_id
                    st.session_state.interrupt_data = interrupt_data
                    st.session_state.active_opp = o
                    st.rerun()

# ---- RIGHT: the draft + approval panel ----
with right:
    st.subheader("Agent draft")
    if "interrupt_data" not in st.session_state:
        st.info("Select an opportunity and click **Run agent** to generate a draft "
                "for review.")
    else:
        data = st.session_state.interrupt_data
        opp = st.session_state.active_opp

        st.markdown(f"**{data['merchant']}** — {data['message_kind']}")
        st.markdown(f"Potential savings: **${data['est_annual_savings']:,.2f}/yr**")

        edited = st.text_area("Message (edit before approving if you like)",
                              value=data["draft_message"], height=320)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Approve", type="primary"):
                status = "edited" if edited != data["draft_message"] else "approved"
                finalize_decision(st.session_state.thread_id, status, edited)
                st.success("Approved. The message is ready for you to send — "
                           "the agent does not send it.")
                reset_draft_state()
                st.rerun()
        with c2:
            if st.button("Reject"):
                finalize_decision(st.session_state.thread_id, "rejected")
                st.warning("Dismissed. No message will be sent.")
                reset_draft_state()
                st.rerun()
        with c3:
            if st.button("Cancel"):
                reset_draft_state()
                st.rerun()
