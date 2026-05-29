"""
16_support_kb.py — Customer Support Knowledge Base with multi-hop reasoning.

Simulates a SaaS support system where Cognee connects FAQs, product docs,
past tickets, and incident postmortems to answer complex questions.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building SaaS Customer Support Knowledge Base...")
    print("=" * 60)

    # ── FAQ data ───────────────────────────────────────────────────────
    await cognee.add("""
    FAQ: Refund Policy — Customers on all plans can request a refund within
    30 days of purchase. Refunds are processed within 5-10 business days.
    Enterprise plan customers have a 60-day refund window. Refund requests
    must be submitted through the billing portal at billing.example.com.

    FAQ: Service Level Agreement (SLA) — Pro plan guarantees 99.9% uptime.
    Enterprise plan guarantees 99.99% uptime. If uptime falls below the SLA,
    customers are eligible for service credits: Pro = 10% of monthly fee per
    0.1% below SLA. Enterprise = 25% of monthly fee per 0.01% below SLA.
    """, dataset_name="support_kb")

    # ── Product documentation ──────────────────────────────────────────
    await cognee.add("""
    PRODUCT DOCS: Payment Processing — ExamplePay supports credit cards,
    ACH transfers, and digital wallets. The payment gateway has a primary
    and fallback endpoint. If the primary endpoint (gateway.example.com)
    fails, the system automatically fails over to the secondary endpoint
    (gateway-fallback.example.com). Payment failures return error codes:
    ERR_401 (auth failure), ERR_503 (gateway unavailable), ERR_422
    (invalid payment method), ERR_429 (rate limited).

    PRODUCT DOCS: User Authentication — The dashboard uses OAuth2 with
    JWT tokens. Tokens expire after 24 hours. SSO is available for
    Enterprise plans via SAML. Login failures can be caused by: expired
    tokens, incorrect SSO configuration, or the auth-service being
    unavailable (returns HTTP 503).
    """, dataset_name="support_kb")

    # ── Past support tickets ───────────────────────────────────────────
    await cognee.add("""
    TICKET #4521 (Resolved) — Pro plan user reported login failure with
    HTTP 503 error on 2026-03-15. Root cause: auth-service pod in
    CrashLoopBackOff due to expired OAuth2 client secret. Resolution:
    rolled back config deployment. Permanent fix: update secret rotation
    pipeline (tracked in ENG-7820).

    TICKET #4610 (Resolved) — Enterprise user reported double-charge on
    March 2026 invoice. Root cause: payment gateway failover triggered
    duplicate transaction when primary gateway returned ERR_503 but
    actually processed the payment. Resolution: refunded duplicate charge;
    updated failover logic to check transaction status before retrying.

    TICKET #4703 (Open) — Multiple Pro users reporting intermittent payment
    failures during checkout. Error: ERR_503. Started 2026-04-01 at 09:15 UTC.
    Affecting approximately 15% of transactions. Incident: INC-0042 opened.
    """, dataset_name="support_kb")

    # ── Incident postmortems ───────────────────────────────────────────
    await cognee.add("""
    INCIDENT POSTMORTEM — INC-0042: Payment Gateway Outage (2026-04-01)
    Duration: 3 hours 45 minutes (09:15-13:00 UTC). Root cause: TLS
    certificate on primary payment gateway expired. The automated cert
    renewal was disabled during a maintenance window on 2026-03-28 and
    not re-enabled. The fallback gateway also had an expired cert because
    it shared the same certificate bundle. Resolution: manually renewed
    certificates and re-enabled auto-renewal. Impact: ~15% of transactions
    failed (estimated 2,300 affected payments). Pro plan uptime dropped
    to 99.83% for April 1 (below 99.9% SLA). Affected customers are
    eligible for service credits: 10% of monthly Pro fee.

    Postmortem action items:
    1. Separate certificate bundles for primary and fallback (ENG-8012)
    2. Add monitoring alert for certificate expiry < 7 days (OPS-342)
    3. Update runbook: never disable auto-renewal without a re-enable ticket
    """, dataset_name="support_kb")

    await cognee.cognify()

    # ── Multi-hop support queries ──────────────────────────────────────
    print("\n── Support Queries ──\n")

    queries = [
        # Single-hop: FAQ lookup
        "What is the refund policy for Pro plan users?",

        # Multi-hop: ticket → root cause → SLA → credits
        "A Pro user affected by the April 1 payment outage wants to know "
        "what caused it, whether they are owed service credits, and how much.",

        # Multi-hop: ticket → similar issue → resolution pattern
        "Has a 503 error on the payment gateway happened before, and what "
        "was the root cause and resolution?",

        # Relationship traversal: incident → action items → engineering tickets
        "What are the outstanding action items from the April 1 incident "
        "and which engineering tickets track them?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! The support KB connects FAQs, docs, tickets, and incidents")
    print("to answer multi-hop questions that flat RAG would miss.")


if __name__ == "__main__":
    asyncio.run(main())
