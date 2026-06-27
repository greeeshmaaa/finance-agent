# Personal Finance Negotiation Agent

An agentic AI system that detects recurring subscriptions, price creep, and
billing anomalies from transaction data, then drafts negotiation and
cancellation messages for human review.

## Safety design
- Uses Plaid **sandbox** data only — no real bank credentials.
- The agent **never sends anything**. It drafts and schedules; a human
  reviews and approves every message. All money-adjacent actions are
  human-in-the-loop by design.

## Status
🚧 In development — Phase 0 complete (env + Postgres).
