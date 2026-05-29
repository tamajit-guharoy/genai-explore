"""
12_permissions.py — Set up multi-user isolation with RBAC.

This example demonstrates dataset-level permissions for a scenario where
two teams (Engineering and HR) share a Cognee instance but must not see
each other's data.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Setting up multi-tenant knowledge base...")
    print("=" * 60)

    # ── Engineering team data ──────────────────────────────────────────
    eng_user = "team_engineering"
    hr_user = "team_hr"

    print(f"\nIngesting Engineering data (user: {eng_user})...")
    await cognee.add(
        "System Architecture: The payment service runs on Kubernetes with "
        "PostgreSQL for persistence. The authentication service uses OAuth2 "
        "with JWT tokens. All services communicate via gRPC. The incident "
        "on March 15, 2026 was caused by a certificate expiration in the "
        "service mesh. Root cause: automated cert rotation disabled during "
        "a maintenance window and not re-enabled.",
        dataset_name="engineering_docs",
        user_id=eng_user,
    )

    print(f"Ingesting HR data (user: {hr_user})...")
    await cognee.add(
        "Employee Handbook: The company offers 25 days of PTO annually. "
        "Parental leave is 16 weeks fully paid. The performance review cycle "
        "runs from January to March each year. Salary bands are reviewed "
        "quarterly. The 401(k) match is 50% up to 6% of salary. Remote work "
        "is available for all roles. The promotion panel meets in Q2 and Q4.",
        dataset_name="hr_docs",
        user_id=hr_user,
    )

    # ── Cognify all users' data ────────────────────────────────────────
    print("\nBuilding knowledge graphs...")
    await cognee.cognify()

    # ── Engineering user queries ───────────────────────────────────────
    print("\n── Engineering team queries ──")
    eng_queries = [
        "What caused the March 15 incident?",
        "What database does the payment service use?",
    ]
    for q in eng_queries:
        results = await cognee.search(q, user_id=eng_user)
        print(f" Q: {q}")
        for r in results:
            print(f"  → {r}")
        print()

    # ── HR user queries ────────────────────────────────────────────────
    print("── HR team queries ──")
    hr_queries = [
        "What is the parental leave policy?",
        "How often are salary bands reviewed?",
    ]
    for q in hr_queries:
        results = await cognee.search(q, user_id=hr_user)
        print(f" Q: {q}")
        for r in results:
            print(f"  → {r}")
        print()

    # ── Isolation verification ─────────────────────────────────────────
    print("── Isolation test ──")

    # Engineering user tries to access HR data
    print(f"Engineering user querying HR topic:")
    results = await cognee.search(
        "What is the PTO policy?",
        user_id=eng_user,
    )
    eng_sees_hr = any("PTO" in str(r) for r in results)
    print(f"  Eng user sees HR data? {' YES — isolation FAILED' if eng_sees_hr else ' NO — isolation works'}")

    # HR user tries to access Engineering data
    print(f"HR user querying Engineering topic:")
    results = await cognee.search(
        "What caused the certificate expiration?",
        user_id=hr_user,
    )
    hr_sees_eng = any("certificate" in str(r).lower() for r in results)
    print(f"  HR user sees Eng data? {' YES — isolation FAILED' if hr_sees_eng else ' NO — isolation works'}")

    print("\nDone! Multi-tenant isolation prevents data leakage between teams.")


if __name__ == "__main__":
    asyncio.run(main())
