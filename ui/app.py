"""
Streamlit approval-queue UI for the Personal Finance Negotiation Agent.

Run with: python -m streamlit run ui/app.py
"""
import streamlit as st
from dotenv import load_dotenv

from ui.service import list_opportunities, draft_for_opportunity, finalize_decision

load_dotenv()

st.set_page_config(page_title="Finance Negotiation Agent", page_icon="◆", layout="wide")

st.markdown("""
<style>
:root {
  --bg: #0E1726;
  --bg2: #0B1320;
  --card: #18283F;
  --card-hover: #1E3050;
  --line: #2C4straight;
  --line: #2C4straight;
  --line: #2A3E5A;
  --blue: #4A90E2;
  --green: #34D399;
  --gold: #E0B341;
  --text: #F2F6FC;
  --text2: #AEBED4;
  --muted: #7388A5;
}

/* Hide Streamlit's default chrome (the white bar, menu, footer) */
header[data-testid="stHeader"] { background: transparent; }
footer { display: none !important; }
.stDeployButton, [data-testid="stDeployButton"] { display: none !important; }

.stApp { background: radial-gradient(1200px 600px at 70% -10%, #15233A 0%, var(--bg) 55%); }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1240px; }

.block-container, .block-container p, .block-container span { color: var(--text); }

.eyebrow {
  text-transform: uppercase; letter-spacing: 0.16em;
  font-size: 0.7rem; color: var(--muted); font-weight: 700;
}
.product-title {
  font-size: 1.45rem; font-weight: 800; color: var(--text);
  letter-spacing: -0.01em; margin-bottom: 1.6rem;
}
.product-title .mark { color: var(--green); }

.hero-number {
  font-size: 4.6rem; font-weight: 800; font-variant-numeric: tabular-nums;
  line-height: 1; color: var(--green);
  text-shadow: 0 0 40px rgba(52,211,153,0.25);
  margin: 0.3rem 0 0.5rem 0;
}
.hero-sub { color: var(--text2); font-size: 0.98rem; max-width: 640px; }

.section-title {
  font-size: 1.15rem; font-weight: 700; color: var(--text);
  margin: 0.5rem 0 1rem 0;
}

/* Cards */
.opp-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 1.15rem 1.3rem 1.25rem 1.3rem;
  margin-bottom: 1rem;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.opp-card:hover { border-color: var(--blue); }
.opp-merchant {
  font-size: 1.18rem; font-weight: 700; color: var(--text) !important;
  margin-bottom: 0.2rem;
}
.opp-meta { color: var(--text2) !important; font-size: 0.88rem; margin-bottom: 0.6rem; }
.opp-savings { font-size: 1.6rem; font-weight: 800; font-variant-numeric: tabular-nums; }
.opp-savings.creep { color: var(--gold); }
.opp-savings.sub { color: var(--green); }
.opp-savings .unit { font-size: 0.78rem; color: var(--muted); font-weight: 600; }

.pill {
  display: inline-block; padding: 0.22rem 0.75rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em; margin-top: 0.65rem;
}
.pill.review { background: rgba(115,136,165,0.2); color: var(--text2); }
.pill.approved { background: rgba(52,211,153,0.18); color: var(--green); }
.pill.dismissed { background: rgba(220,110,110,0.18); color: #E59A9A; }

/* Streamlit buttons restyled to match cards */
.stButton > button {
  border-radius: 10px; font-weight: 600;
  background: var(--card); color: var(--text);
  border: 1px solid var(--line); padding: 0.45rem 1rem;
  transition: all 0.15s ease;
}
.stButton > button:hover {
  border-color: var(--blue); background: var(--card-hover); color: var(--text);
}
.stButton > button[kind="primary"] {
  background: var(--green); color: #08210F; border: none;
}
.stButton > button[kind="primary"]:hover { background: #2BC089; color: #08210F; }

/* Draft panel */
.draft-card {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 16px; padding: 1.3rem;
}
.draft-head { font-size: 1.25rem; font-weight: 700; color: var(--text); }
.draft-sub { color: var(--text2); font-size: 0.9rem; margin: 0.2rem 0 0.9rem 0; }

.empty-panel {
  background: var(--card); border: 1px dashed var(--line);
  border-radius: 16px; padding: 2rem; color: var(--text2);
  text-align: center; font-size: 0.95rem;
}

textarea {
  background: var(--bg2) !important; color: var(--text) !important;
  border-radius: 10px !important; border: 1px solid var(--line) !important;
  font-family: ui-monospace, monospace !important; font-size: 0.86rem !important;
}
</style>
""", unsafe_allow_html=True)

STATUS_PILL = {
    "detected": '<span class="pill review">Needs review</span>',
    "approved_ready_to_send": '<span class="pill approved">Approved · ready to send</span>',
    "dismissed": '<span class="pill dismissed">Dismissed</span>',
}
TYPE_LABELS = {"price_creep": "Price increase", "recurring_subscription": "Recurring subscription"}


def reset_draft_state():
    for k in ("thread_id", "interrupt_data", "active_opp"):
        st.session_state.pop(k, None)


opportunities = list_opportunities()
active = [o for o in opportunities if o["status"] != "dismissed"]
total_potential = sum(o["est_annual_savings"] for o in active)
reviewed = sum(1 for o in opportunities if o["status"] != "detected")

# Hero
st.markdown('<div class="product-title"><span class="mark">◆</span> Finance Negotiation Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow" style="margin-top:1.5rem">Potential annual savings found</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-number">${total_potential:,.0f}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="hero-sub">{len(opportunities)} opportunities detected · {reviewed} reviewed. '
    f'The agent researches each merchant and drafts a message for your approval — '
    f'it never sends anything itself.</div>',
    unsafe_allow_html=True,
)
st.write("")
st.write("")

left, right = st.columns([1, 1.1], gap="large")

with left:
    st.markdown('<div class="section-title">Opportunities</div>', unsafe_allow_html=True)
    for o in opportunities:
        is_creep = o["opportunity_type"] == "price_creep"
        cls = "creep" if is_creep else "sub"
        meta = f'{TYPE_LABELS[o["opportunity_type"]]} · ${o["current_price"]:.2f}/mo'
        if is_creep and o.get("prior_price"):
            meta += f' · was ${o["prior_price"]:.2f}'
        st.markdown(f"""
<div class="opp-card">
  <div class="opp-merchant">{o['merchant']}</div>
  <div class="opp-meta">{meta}</div>
  <div class="opp-savings {cls}">${o['est_annual_savings']:,.0f}<span class="unit">/yr</span></div>
  {STATUS_PILL.get(o['status'], '')}
</div>
""", unsafe_allow_html=True)
        if o["status"] == "detected":
            if st.button(f"Run agent on {o['merchant']} →", key=f"run-{o['id']}", use_container_width=True):
                reset_draft_state()
                with st.spinner(f"Researching {o['merchant']} and drafting…"):
                    tid, idata = draft_for_opportunity(o["id"])
                st.session_state.thread_id = tid
                st.session_state.interrupt_data = idata
                st.session_state.active_opp = o
                st.rerun()

with right:
    st.markdown('<div class="section-title">Agent draft</div>', unsafe_allow_html=True)
    if "interrupt_data" not in st.session_state:
        st.markdown(
            '<div class="empty-panel">No draft yet.<br>Pick an opportunity on the left '
            'and run the agent to see a researched, ready-to-review message here.</div>',
            unsafe_allow_html=True,
        )
    else:
        data = st.session_state.interrupt_data
        kind = data["message_kind"].capitalize()
        st.markdown(f'<div class="draft-head">{data["merchant"]} · {kind}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="draft-sub">Potential savings ${data["est_annual_savings"]:,.0f}/yr · '
            f'edit the message below before approving.</div>',
            unsafe_allow_html=True,
        )
        edited = st.text_area("Message", value=data["draft_message"], height=340, label_visibility="collapsed")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✓ Approve", type="primary", use_container_width=True):
                status = "edited" if edited != data["draft_message"] else "approved"
                finalize_decision(st.session_state.thread_id, status, edited)
                st.success("Approved — ready for you to send. The agent does not send it.")
                reset_draft_state()
                st.rerun()
        with c2:
            if st.button("Dismiss", use_container_width=True):
                finalize_decision(st.session_state.thread_id, "rejected")
                reset_draft_state()
                st.rerun()
        with c3:
            if st.button("Cancel", use_container_width=True):
                reset_draft_state()
                st.rerun()
