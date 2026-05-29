"""
Example 20: Customer Support Agent with Temporal Memory (FULL WORKING SIMULATION)

This example simulates a multi-turn customer support conversation spanning 3
sessions over 2 weeks. The support agent uses Graphiti's temporal knowledge
graph to:

  - Remember past interactions with the same user (via group_id)
  - Connect issues across sessions (multi-hop reasoning)
  - Track what solutions have been tried and what worked
  - Update its knowledge when issues are resolved
  - Query temporal context: "what issues has this user had?"
  - Answer multi-hop questions: "what solution worked for the login bug?"

The scenario:
  - Session 1 (Day 1):  User reports a login bug, agent investigates, finds workaround
  - Session 2 (Day 7):  User reports a payment issue, agent recalls login history,
                        connects dots to account problem
  - Session 3 (Day 14): User confirms everything resolved, agent updates knowledge

Each session prints the agent's internal reasoning process.
"""

import asyncio
import os
import socket
import sys
import textwrap

from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Environment / connectivity check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti needs an LLM for extraction.\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    host, _, port_str = NEO4J_URI.replace("bolt://", "").replace("neo4j://", "").partition(":")
    try:
        port = int(port_str) if port_str else 7687
    except ValueError:
        port = 7687
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


# ===================================================================
# Support Agent (simulated)
# ===================================================================

class SupportAgent:
    """
    A simulated customer support agent backed by a Graphiti knowledge graph.
    The agent stores every interaction as episodes and queries the graph to
    recall past context, connect issues, and track resolution status.
    """

    def __init__(self, graphiti, user_group_id: str):
        self.graphiti = graphiti
        self.user_group_id = user_group_id
        self.user_name = "Alex Thompson"

    # ------------------------------------------------------------------
    # Internal reasoning (printed to show the agent's thought process)
    # ------------------------------------------------------------------
    def _reason(self, step: str, detail: str = ""):
        """Print a reasoning step as if the agent is thinking aloud."""
        print(f"  [AGENT REASONING] {step}")
        if detail:
            for line in textwrap.wrap(detail, width=66):
                print(f"    {line}")

    # ------------------------------------------------------------------
    # Session 1: User reports login bug
    # ------------------------------------------------------------------
    async def session_1_login_issue(self, current_time: datetime):
        """Day 1: User reports being unable to log in."""
        print("\n" + "=" * 72)
        print(f"SESSION 1 (Day 1): User reports login bug")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        # -- Step 1: Receive the issue --
        self._reason(
            "NEW ISSUE RECEIVED",
            f"User {self.user_name} reports: 'I keep getting an error when trying to "
            "log in. It says \"authentication token expired\" even right after I log in. "
            "This started happening this morning.'"
        )

        # -- Step 2: Check if this user has past issues --
        self._reason(
            "CHECKING USER HISTORY",
            "Querying knowledge graph for past issues related to this user..."
        )
        past_issues = await self.graphiti.search(
            query=f"What issues has {self.user_name} reported?",
            group_ids=[self.user_group_id],
            num_results=5,
        )

        if past_issues:
            self._reason("FOUND PAST ISSUES", f"Found {len(past_issues)} past records.")
            for issue in past_issues:
                print(f"    Recall: {issue.fact}")
        else:
            self._reason("NO PAST ISSUES", "This is the first issue reported by this user.")

        # -- Step 3: Store the issue in the graph --
        self._reason(
            "STORING ISSUE IN KNOWLEDGE GRAPH",
            "Adding episode about the login bug with full details."
        )
        await self.graphiti.add_episode(
            name="login_bug_report",
            episode_body=(
                f"{self.user_name} reported a login bug. The error message is "
                "'authentication token expired'. The issue occurs immediately after "
                "logging in. This started happening on {current_time.strftime('%Y-%m-%d')}. "
            ),
            source="support_ticket",
            source_description="Support ticket #TKT-1001: Login authentication issue",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: login_bug_report")

        # -- Step 4: Investigate --
        self._reason(
            "INVESTIGATING ROOT CAUSE",
            "Checking if the issue is related to recent account changes, SSO "
            "configuration, or session timeout settings..."
        )
        # Simulated investigation result
        self._reason(
            "INVESTIGATION RESULT",
            "Discovered that the session token lifetime was set to 0 seconds due to "
            "a misconfigured deployment flag. This causes tokens to expire immediately."
        )

        # -- Step 5: Store the root cause --
        await self.graphiti.add_episode(
            name="login_bug_root_cause",
            episode_body=(
                f"Root cause of {self.user_name}'s login bug: session token lifetime "
                "was misconfigured to 0 seconds during a deployment on "
                f"{current_time.strftime('%Y-%m-%d')}. This caused immediate token expiration."
            ),
            source="support_investigation",
            source_description="Engineering analysis of TKT-1001",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: login_bug_root_cause")

        # -- Step 6: Find and store workaround --
        self._reason(
            "DEVISING WORKAROUND",
            "Token lifetime setting is controlled by an environment variable SESSION_TTL. "
            "Resetting it to 3600 seconds (1 hour) should fix it until the deployment "
            "pipeline is fixed."
        )
        await self.graphiti.add_episode(
            name="login_bug_workaround",
            episode_body=(
                f"Workaround for {self.user_name}'s login bug: reset SESSION_TTL "
                "environment variable to 3600 seconds (1 hour). This bypasses the "
                "misconfigured deployment flag. Permanent fix requires updating the "
                "deployment pipeline to not override SESSION_TTL."
            ),
            source="support_resolution",
            source_description="Applied hotfix for TKT-1001",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: login_bug_workaround (workaround applied)")

        # -- Print response to user --
        print("\n  [AGENT RESPONSE TO USER]")
        print("  " + "-" * 60)
        print(
            "  Hi Alex, I've investigated the login issue. It turns out a recent\n"
            "  deployment misconfigured the session token lifetime. I've applied a\n"
            "  hotfix that resets it to 1 hour. You should be able to log in now.\n"
            "  A permanent fix will be deployed in the next release. Ticket TKT-1001."
        )

    # ------------------------------------------------------------------
    # Session 2: User reports payment issue (agent connects the dots)
    # ------------------------------------------------------------------
    async def session_2_payment_issue(self, current_time: datetime):
        """Day 7: User reports a payment issue. Agent recalls login history."""
        print("\n" + "=" * 72)
        print(f"SESSION 2 (Day 7): User reports payment issue")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        # -- Step 1: Receive new issue --
        self._reason(
            "NEW ISSUE RECEIVED",
            f"User {self.user_name} reports: 'My payment of $49.99 for the premium "
            "plan failed. The system says \"payment gateway authentication error\". "
            "I tried two different credit cards.'"
        )

        # -- Step 2: Check user history (temporal query) --
        self._reason(
            "QUERYING USER HISTORY (TEMPORAL)",
            "Searching knowledge graph for ALL past issues reported by this user..."
        )

        temporal_query = "What issues has Alex Thompson experienced?",
        past_issues = await self.graphiti.search(
            query=temporal_query,
            group_ids=[self.user_group_id],
            num_results=10,
        )

        if past_issues:
            self._reason(
                "RETRIEVED PAST CONTEXT",
                f"Found {len(past_issues)} relevant records from past sessions."
            )
            for i, issue in enumerate(past_issues, 1):
                valid_str = issue.valid_at.strftime('%Y-%m-%d') if issue.valid_at else "unknown"
                expiry_str = issue.invalid_at.strftime('%Y-%m-%d') if issue.invalid_at else "current"
                print(f"    [{i}] [{valid_str} -> {expiry_str}] {issue.fact}")
        else:
            self._reason("NO PAST CONTEXT", "No relevant past records found.")

        # -- Step 3: Multi-hop reasoning --
        self._reason(
            "MULTI-HOP REASONING",
            "Analyzing connection between current payment issue and past login issue...\n"
            "  Hop 1: Login bug was caused by misconfigured session token lifetime.\n"
            "  Hop 2: Session tokens are also used for payment gateway authentication.\n"
            "  Connection: The SESSION_TTL fix from last week may have been overwritten\n"
            "    by a subsequent deployment, OR the same deployment pipeline bug\n"
            "    is now affecting the payment gateway configuration.\n"
            "  Conclusion: Both issues may stem from the same root cause -- the\n"
            "    deployment pipeline that misconfigures authentication-related settings."
        )

        # -- Step 4: Store payment issue --
        await self.graphiti.add_episode(
            name="payment_issue_report",
            episode_body=(
                f"{self.user_name} reported a payment failure for the premium plan "
                "($49.99). Error: 'payment gateway authentication error'. Two different "
                "credit cards were tried. This appears related to the previous login "
                "issue: both involve authentication token configuration. The deployment "
                "pipeline may be overwriting both SESSION_TTL and payment gateway auth settings."
            ),
            source="support_ticket",
            source_description="Support ticket #TKT-1007: Payment authentication failure",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: payment_issue_report (linked to login bug)")

        # -- Step 5: Connect the issues --
        self._reason(
            "CONNECTING ISSUES IN KNOWLEDGE GRAPH",
            "Adding explicit relationship between the login bug and payment issue to "
            "help future queries connect the dots."
        )
        # Add an episode that explicitly links the two issues
        await self.graphiti.add_episode(
            name="issues_connected",
            episode_body=(
                f"Connection found: {self.user_name}'s login bug (TKT-1001) and payment "
                "authentication failure (TKT-1007) share a common root cause. Both are caused "
                "by the deployment pipeline overwriting authentication token settings. "
                "The login bug was patched with a SESSION_TTL=3600 workaround, but a "
                "subsequent deployment on "
                f"{(current_time - timedelta(days=1)).strftime('%Y-%m-%d')} "
                "re-introduced the issue and also broke payment gateway auth."
            ),
            source="support_analysis",
            source_description="Engineering analysis linking TKT-1001 and TKT-1007",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: issues_connected (multi-hop link)")

        # -- Step 6: Store the solution --
        self._reason(
            "APPLYING FIX",
            "Fixing the deployment pipeline to preserve authentication-related "
            "environment variables. Also patching the payment gateway config."
        )
        await self.graphiti.add_episode(
            name="payment_issue_fix",
            episode_body=(
                f"Fix applied for {self.user_name}'s payment issue: updated the deployment "
                "pipeline to not overwrite SESSION_TTL, PAYMENT_AUTH_KEY, or "
                "GATEWAY_TOKEN settings. Payment gateway re-authenticated successfully. "
                "Changes deployed and verified."
            ),
            source="support_resolution",
            source_description="Applied fix for TKT-1007",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: payment_issue_fix")

        # -- Print response to user --
        print("\n  [AGENT RESPONSE TO USER]")
        print("  " + "-" * 60)
        print(
            "  Hi Alex, I found the issue! It's related to the login problem you had\n"
            "  last week. The same deployment pipeline bug that caused the login issue\n"
            "  also broke the payment gateway authentication. I've fixed the pipeline\n"
            "  and your payment should go through now. I've also verified both fixes are\n"
            "  working together. Ticket TKT-1007."
        )

    # ------------------------------------------------------------------
    # Session 3: User confirms resolved, agent updates knowledge
    # ------------------------------------------------------------------
    async def session_3_resolution_confirmation(self, current_time: datetime):
        """Day 14: User confirms everything is working."""
        print("\n" + "=" * 72)
        print(f"SESSION 3 (Day 14): User confirms resolved")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        # -- Step 1: Receive confirmation --
        self._reason(
            "USER CONFIRMATION RECEIVED",
            f"User {self.user_name} reports: 'Everything is working now! I can log in "
            "and my premium payment went through. Thanks for the help!'"
        )

        # -- Step 2: Update the graph with resolution status --
        self._reason(
            "UPDATING KNOWLEDGE GRAPH",
            "Marking both issues as resolved in the graph. Adding final resolution "
            "episode that captures the full story."
        )
        await self.graphiti.add_episode(
            name="all_issues_resolved",
            episode_body=(
                f"All issues for {self.user_name} are now resolved. Two issues were "
                "connected: a login authentication bug (TKT-1001) and a payment gateway "
                "authentication failure (TKT-1007). Both were caused by a deployment "
                "pipeline that overwrote authentication token settings. Resolution: "
                "deployment pipeline updated to preserve auth settings, SESSION_TTL set "
                "to 3600s, payment gateway re-authenticated. User confirmed all working."
            ),
            source="support_resolution",
            source_description="Case closed: both TKT-1001 and TKT-1007 resolved",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Episode stored: all_issues_resolved (case closed)")

        # -- Step 3: Query the full resolution path --
        self._reason(
            "QUERYING FULL RESOLUTION PATH",
            "Verifying that the knowledge graph can trace the complete story..."
        )

        resolution_queries = [
            "What issues did Alex Thompson have?",
            "What solution worked for the login bug?",
            "What was the connection between the login bug and payment issue?",
        ]

        for query in resolution_queries:
            print(f'\n    Query: "{query}"')
            edges = await self.graphiti.search(
                query=query,
                group_ids=[self.user_group_id],
                num_results=3,
            )
            if edges:
                for i, edge in enumerate(edges, 1):
                    print(f"      [{i}] {edge.fact}")
            else:
                print("      (no results)")

        # -- Print response to user --
        print("\n  [AGENT RESPONSE TO USER]")
        print("  " + "-" * 60)
        print(
            "  That's great to hear, Alex! I'm glad everything is working smoothly now.\n"
            "  I've documented the full resolution in my knowledge base, so if you ever\n"
            "  have similar issues in the future, I'll be able to recall exactly what\n"
            "  worked. Both tickets TKT-1001 and TKT-1007 are now closed. Thanks for\n"
            "  your patience while we resolved this!"
        )


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 20: Customer Support Agent with Temporal Memory")
    print("=" * 72)
    print(
        "\n"
        "  This simulation demonstrates a support agent that:\n"
        "  - Remembers past interactions across sessions (temporal memory)\n"
        "  - Connects seemingly unrelated issues (multi-hop reasoning)\n"
        "  - Tracks what solutions worked (resolution knowledge)\n"
        "  - Updates its knowledge when issues are resolved\n"
        "\n"
        "  Scenario: A user has 3 support sessions over 14 days.\n"
        "  Group ID isolates this user's data from other users.\n"
    )

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    # Each user gets their own group_id for data isolation
    user_group_id = "user_alex_thompson"

    # Create the support agent
    agent = SupportAgent(graphiti, user_group_id)

    # Timeline: start 14 days ago
    base_time = datetime.now(timezone.utc) - timedelta(days=14)

    # -- Session 1 (Day 1) -------------------------------------------------
    day_1 = base_time
    await agent.session_1_login_issue(day_1)

    # -- Session 2 (Day 7) -------------------------------------------------
    day_7 = base_time + timedelta(days=7)
    await agent.session_2_payment_issue(day_7)

    # -- Session 3 (Day 14) ------------------------------------------------
    day_14 = base_time + timedelta(days=14)
    await agent.session_3_resolution_confirmation(day_14)

    # ------------------------------------------------------------------
    # Final demonstration: temporal and multi-hop queries
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("TEMPORAL MEMORY DEMONSTRATION")
    print("=" * 72)

    print(
        "\n"
        "  The knowledge graph can now answer temporal queries and trace\n"
        "  multi-hop relationships. Let's demonstrate both:\n"
    )

    # -- Temporal query --
    print("\n  --- Temporal Query: 'What issues did this user have?' ---")
    temporal_results = await graphiti.search(
        query="What issues did Alex Thompson have throughout their support journey?",
        group_ids=[user_group_id],
        num_results=5,
    )
    if temporal_results:
        for i, r in enumerate(temporal_results, 1):
            print(f"    [{i}] {r.fact}")
            if r.valid_at:
                print(f"        When: {r.valid_at.strftime('%Y-%m-%d')}")
            if r.invalid_at:
                print(f"        Resolved: {r.invalid_at.strftime('%Y-%m-%d')}")
    else:
        print("    (no temporal results)")

    # -- Multi-hop query --
    print("\n  --- Multi-Hop Query: 'What solution worked for the login bug?' ---")
    multi_hop_results = await graphiti.search(
        query="What solution worked for the login bug that Alex Thompson reported?",
        group_ids=[user_group_id],
        num_results=5,
    )
    if multi_hop_results:
        for i, r in enumerate(multi_hop_results, 1):
            print(f"    [{i}] {r.fact}")
    else:
        print("    (no multi-hop results)")

    # -- Cleanup ------------------------------------------------------------
    await graphiti.close()
    print("\n" + "=" * 72)
    print("Simulation complete. Closed Graphiti connection.")
    print(
        "\n"
        "  KEY TAKEAWAYS:\n"
        "  - group_id isolates data per user (multi-tenant support)\n"
        "  - Episodes across time let the agent recall past context\n"
        "  - Multi-hop reasoning connects separate issues automatically\n"
        "  - The graph remembers even after issues are resolved\n"
        "  - Temporal queries answer 'what happened and when'"
    )


if __name__ == "__main__":
    asyncio.run(main())
