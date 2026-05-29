"""
20_financial_intel.py — Financial Intelligence & Supply Chain Analysis.

Simulates ingesting earnings reports, news, and filings to enable multi-hop
supply chain and market impact analysis.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building Financial Intelligence Knowledge Graph...")
    print("=" * 60)

    # ── Company profiles ───────────────────────────────────────────────
    await cognee.add("""
    COMPANY PROFILES:

    Apple Inc. (AAPL) — Consumer electronics and services. FY2025 revenue:
    $395B. Key products: iPhone (52% of revenue), Mac, iPad, Services, Wearables.
    Market cap: $3.2T. Major suppliers: TSMC (chips), Foxconn (assembly),
    Samsung (displays), Broadcom (wireless components).

    TSMC (Taiwan Semiconductor Manufacturing Co, TSM) — World's largest
    semiconductor foundry. 60% global market share in contract chip manufacturing.
    FY2025 revenue: $85B. Key customers: Apple (25% of revenue), NVIDIA (15%),
    AMD (10%), Qualcomm (8%). TSMC's advanced 3nm chips are produced exclusively
    in Taiwan, with new fabs under construction in Arizona (USA) and Kumamoto
    (Japan).

    Foxconn (Hon Hai Precision, 2317.TW) — World's largest electronics contract
    manufacturer. FY2025 revenue: $210B. Key customer: Apple (~50% of revenue).
    Major factories in: Zhengzhou (China), Chennai (India), and Vietnam.
    """, dataset_name="financial")

    # ── News events (temporal) ─────────────────────────────────────────
    await cognee.add("""
    NEWS — March 15, 2026:
    The U.S. Department of Commerce announced new export controls on advanced
    semiconductor manufacturing equipment to China, effective April 1, 2026.
    The controls specifically target equipment used in sub-7nm chip production.
    TSMC said the controls will not directly affect its operations as its most
    advanced fabs are in Taiwan. However, analysts warn that increased
    geopolitical tension could disrupt TSMC's supply of raw materials and
    equipment from U.S. and Dutch suppliers.

    NEWS — March 20, 2026:
    A 7.4 magnitude earthquake struck southern Taiwan, temporarily disrupting
    operations at TSMC's Tainan fab. TSMC stated that no critical equipment
    was damaged but wafer production was halted for 48 hours. Analysts estimate
    the disruption could reduce Q1 2026 output by 1-2%, potentially affecting
    chip supply to Apple and NVIDIA. TSMC shares fell 3.2% on the news.
    """, dataset_name="financial")

    await cognee.add("""
    NEWS — April 5, 2026:
    Apple announced plans to accelerate its shift of iPhone production from
    China to India. Foxconn's Chennai facility will expand capacity by 40%
    by end of 2026. This follows ongoing U.S.-China trade tensions and supply
    chain diversification efforts. Apple aims to produce 25% of iPhones in
    India by 2027, up from 12% in 2025.

    NEWS — April 10, 2026:
    The Taiwan earthquake impact is becoming clearer: TSMC reports that 3nm
    wafer output will be 3% below guidance for Q1 2026. Apple, which uses
    TSMC's 3nm process for its A19 and M5 chips, may face minor supply
    constraints for next-generation products. However, TSMC's Arizona fab
    (producing 4nm chips) was unaffected and remains on schedule to begin
    volume production in H2 2026.
    """, dataset_name="financial")

    await cognee.add("""
    NEWS — May 1, 2026:
    New tariffs announced: The U.S. imposed a 25% tariff on electronics
    imported from China, including smartphones and laptops. Taiwan-made
    semiconductors are exempt. This creates a split impact for Apple:
    iPhones assembled in China face 25% tariff (affecting ~75% of iPhone
    production), while iPhones assembled in India and Vietnam are unaffected.
    Foxconn's ongoing capacity shift to India is now seen as strategically
    critical. Apple shares fell 1.8%.

    ANALYSIS — May 5, 2026:
    Supply chain impact assessment: The combination of Taiwan earthquake
    disruption (1-3% chip output reduction) and China tariffs (affecting
    ~75% of Apple's iPhone assembly) presents a compounding supply chain
    challenge. Mitigating factors: TSMC's Arizona fab coming online, Foxconn's
    India expansion, and Apple's $50B cash reserve enabling rapid supply
    chain restructuring. Risk rating: MODERATE (near-term), DECLINING (2027+).
    """, dataset_name="financial")

    await cognee.cognify()

    # ── Multi-hop financial queries ────────────────────────────────────
    print("\n── Financial Intelligence Queries ──\n")

    queries = [
        # Direct impact
        "How does the Taiwan earthquake affect Apple's chip supply?",

        # Multi-hop supply chain
        "Which of Apple's products are most vulnerable to the combination of "
        "the Taiwan earthquake and the China tariffs?",

        # Supplier exposure
        "How exposed is TSMC to geopolitical risks in Taiwan, and what "
        "mitigations are in place?",

        # Temporal analysis
        "Trace the sequence of events from March to May 2026 that have "
        "affected Apple's supply chain. What is the cumulative impact?",

        # Strategy assessment
        "How is Apple mitigating its China dependency, and at what pace?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! Multi-hop supply chain analysis connects companies, events,")
    print("and risks that would be spread across dozens of news articles.")


if __name__ == "__main__":
    asyncio.run(main())
