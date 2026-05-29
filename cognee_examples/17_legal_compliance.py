"""
17_legal_compliance.py — Legal Document & Compliance Analysis.

Simulates contract analysis with clause-level extraction, obligation tracking,
and cross-referencing against regulations like GDPR.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building Legal Document Knowledge Graph...")
    print("=" * 60)

    # ── Contract 1: Data Processing Agreement ──────────────────────────
    await cognee.add("""
    DATA PROCESSING AGREEMENT (DPA)
    Between: DataController Inc. ("Controller") and CloudProcessor Ltd ("Processor")
    Effective Date: January 1, 2025
    Term: 36 months (expires December 31, 2027)
    Governing Law: California, USA

    Clause 4.1 — Data Processing: Processor shall process personal data only
    on documented instructions from Controller. Processing shall be limited
    to the purpose of providing cloud hosting services.

    Clause 4.2 — Data Subject Rights: Processor shall assist Controller in
    responding to data subject access requests (DSARs) within 72 hours.
    Processor must notify Controller of any DSAR received directly within
    24 hours.

    Clause 4.3 — Security Measures: Processor shall implement and maintain
    appropriate technical and organizational measures including: encryption
    at rest and in transit, access controls with multi-factor authentication,
    regular penetration testing (quarterly), and an incident response plan.

    Clause 5.1 — Sub-processors: Controller authorizes Processor to engage
    the following sub-processors: AWS (infrastructure), Datadog (monitoring),
    and SendGrid (email notifications). Processor must notify Controller
    30 days before adding new sub-processors.

    Clause 5.2 — Liability: Processor's total liability under this DPA is
    capped at $2,000,000 or 12 months of fees, whichever is greater.

    Clause 6.1 — Breach Notification: In the event of a personal data breach,
    Processor shall notify Controller within 24 hours of becoming aware.
    Notification shall include: nature of the breach, categories and
    approximate number of data subjects affected, likely consequences,
    and measures taken or proposed to address the breach.
    """, dataset_name="legal")

    # ── Contract 2: Vendor Agreement ───────────────────────────────────
    await cognee.add("""
    VENDOR SERVICES AGREEMENT
    Between: DataController Inc. ("Client") and AnalyticsPro LLC ("Vendor")
    Effective Date: March 15, 2025
    Term: 24 months (expires March 14, 2027)
    Governing Law: Delaware, USA

    Clause 3.1 — Services: Vendor shall provide user behavior analytics
    by processing Client's customer interaction data. This includes page
    views, click streams, session recordings, and purchase history.

    Clause 3.2 — Data Storage: All data shall be stored within the United
    States. Vendor shall not transfer data outside the US without prior
    written consent from Client.

    Clause 7.1 — Data Retention: Vendor shall retain data for the duration
    of the agreement plus 90 days. Upon termination, Vendor shall delete
    all Client data within 30 days and provide a certificate of deletion.

    Clause 8.1 — Security: Vendor shall maintain SOC 2 Type II certification
    and conduct annual penetration testing. Encryption is required for
    data in transit (TLS 1.3) and at rest (AES-256).

    Clause 9.1 — Breach Notification: Vendor shall notify Client within
    48 hours of discovering a security incident involving Client data.

    Clause 10.1 — Liability Cap: $500,000 aggregate.
    """, dataset_name="legal")

    # ── Regulation: GDPR excerpts ──────────────────────────────────────
    await cognee.add("""
    GDPR KEY PROVISIONS:

    Article 17 — Right to Erasure ("Right to be Forgotten"): Data subjects
    have the right to obtain erasure of personal data without undue delay.
    Controllers must respond within 30 days. This applies when: data is no
    longer necessary, consent is withdrawn, data was unlawfully processed,
    or a legal obligation requires erasure.

    Article 28 — Processor Obligations: Processors must: (a) process only
    on documented instructions, (b) ensure confidentiality, (c) implement
    appropriate security measures, (d) obtain controller consent for
    sub-processors, (e) assist with DSARs, (f) assist with security breach
    notifications, (g) delete or return data at end of contract.

    Article 32 — Security of Processing: Requires "appropriate technical
    and organizational measures" including: pseudonymization and encryption,
    ability to ensure ongoing confidentiality and integrity, ability to
    restore availability and access, regular testing and evaluating of
    security measures.

    Article 33 — Breach Notification: Notification to supervisory authority
    within 72 hours of becoming aware of a breach, unless the breach is
    unlikely to result in risk to individuals.
    """, dataset_name="legal")

    await cognee.cognify()

    # ── Compliance queries ─────────────────────────────────────────────
    print("\n── Compliance Analysis ──\n")

    queries = [
        # Contract comparison
        "Compare the breach notification timelines required in the CloudProcessor "
        "DPA vs the AnalyticsPro agreement. Which is more stringent?",

        # Cross-reference contracts vs regulation
        "Do the security measures in both vendor contracts meet GDPR Article 32 "
        "requirements? What gaps exist?",

        # Obligation tracking
        "What are all the obligations of CloudProcessor Ltd as a data processor?",

        # Risk identification
        "The AnalyticsPro agreement has a data retention clause — does this "
        "conflict with GDPR Article 17 (Right to Erasure)?",

        # Multi-contract analysis
        "Which contracts reference sub-processors and what approval rights "
        "does the Controller have over them?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! Cross-referencing contracts against regulations is exactly")
    print("the kind of multi-document reasoning Cognee excels at.")


if __name__ == "__main__":
    asyncio.run(main())
