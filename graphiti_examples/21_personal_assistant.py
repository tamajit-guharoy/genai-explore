"""
Example 21: Personal Assistant with Preference Learning (FULL WORKING SIMULATION)

This example simulates an AI personal assistant that learns about a user over
4 weeks and uses Graphiti's temporal knowledge graph to:

  - Store user preferences as structured knowledge
  - Detect when preferences are contradicted and expire (not delete) old ones
  - Learn multi-step procedures from natural conversation
  - Accumulate knowledge across weeks to personalize responses
  - Proactively assist based on learned preferences and routines

The simulated interaction:
  - Week 1: User mentions initial preferences (dark mode, email, work hours)
  - Week 2: User adds/changes preferences (Slack for urgent, contradicts email pref)
  - Week 3: User teaches the assistant a procedure (weekly report preparation)
  - Week 4: Assistant proactively helps using accumulated knowledge

This demonstrates how a temporal knowledge graph enables an assistant to
build a persistent, evolving model of a user over time.
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
# Personal Assistant (simulated)
# ===================================================================

class PersonalAssistant:
    """
    A simulated AI personal assistant that learns about a user over time.
    It stores everything in Graphiti and queries its own memory to
    personalize interactions.
    """

    def __init__(self, graphiti, user_group_id: str):
        self.graphiti = graphiti
        self.user_group_id = user_group_id
        self.user_name = "Jordan"

    def _speak(self, message: str):
        """Print the assistant's response to the user."""
        print(f"\n  [ASSISTANT]")
        for line in textwrap.wrap(message, width=66):
            print(f"    {line}")

    def _reason(self, step: str, detail: str = ""):
        """Print the assistant's internal reasoning."""
        print(f"  [INTERNAL THOUGHT] {step}")
        if detail:
            for line in textwrap.wrap(detail, width=66):
                print(f"    {line}")

    async def _query_memory(self, question: str) -> list:
        """Query the knowledge graph for relevant memories."""
        results = await self.graphiti.search(
            query=question,
            group_ids=[self.user_group_id],
            num_results=5,
        )
        return results

    def _print_memories(self, memories: list, heading: str = ""):
        """Pretty-print retrieved memories."""
        if heading:
            print(f"    --- {heading} ---")
        if not memories:
            print("    (no relevant memories found)")
            return
        for i, m in enumerate(memories, 1):
            valid_str = m.valid_at.strftime('%a %Y-%m-%d') if m.valid_at else "unknown"
            expiry_str = m.invalid_at.strftime('%a %Y-%m-%d') if m.invalid_at else "current"
            print(f"    [{i}] [{valid_str} -> {expiry_str}] {m.fact}")

    # ==============================================================
    #  Week 1: User mentions initial preferences
    # ==============================================================
    async def week_1_preference_introduction(self, current_time: datetime):
        """The user introduces themselves and shares preferences."""
        week_num = 1
        print("\n" + "=" * 72)
        print(f"WEEK {week_num}: User introduces preferences")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        self._speak(
            "Hi Jordan! I'm your AI assistant. Feel free to tell me about "
            "yourself, your preferences, and how you like to work. I'll "
            "remember everything to personalize our interactions."
        )

        # Simulate user messages and store each as an episode
        user_messages = [
            (
                "preference_dark_mode",
                f"{self.user_name} prefers dark mode in all applications. "
                f"{self.user_name} finds light mode causes eye strain, especially "
                "when working late."
            ),
            (
                "preference_communication",
                f"{self.user_name} prefers email over Slack for non-urgent "
                "communication. {self.user_name} checks email every morning at 9 AM "
                "and finds Slack notifications distracting during deep work."
            ),
            (
                "preference_work_hours",
                f"{self.user_name} works from 9 AM to 5 PM Eastern Time, Monday "
                "through Friday. {self.user_name} does not check work messages "
                "on weekends."
            ),
        ]

        for name, body in user_messages:
            self._reason(f"LEARNING PREFERENCE: {name}", f"Extracting and storing: {body[:80]}...")
            await self.graphiti.add_episode(
                name=name,
                episode_body=body,
                source="user_preference",
                source_description=f"Preference shared by {self.user_name}",
                reference_time=current_time,
                group_id=self.user_group_id,
            )
            print(f"    Stored: {name}")

        self._speak(
            "Great, I've noted your preferences! I'll use dark mode when displaying "
            "information, use email for non-urgent communication, and respect your "
            "9-5 Eastern Time work hours. I'll avoid disturbing you on weekends."
        )

    # ==============================================================
    #  Week 2: User changes some preferences (contradiction)
    # ==============================================================
    async def week_2_preference_evolution(self, current_time: datetime):
        """User adds preferences -- some contradicting week 1."""
        week_num = 2
        print("\n" + "=" * 72)
        print(f"WEEK {week_num}: Preferences evolve (some contradicted)")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        # First, show the assistant recalling what it knows
        self._reason(
            "RECALLING KNOWN PREFERENCES",
            "Before processing new input, checking what I already know about Jordan..."
        )
        known_prefs = await self._query_memory("What are Jordan's preferences?")
        self._print_memories(known_prefs, "EXISTING PREFERENCES (from Week 1)")

        self._speak(
            "Hi Jordan! I see from last week that you prefer email and dark mode, "
            "and work 9-5 ET. What would you like to add or change?"
        )

        # Now the user shares new preferences, one of which contradicts week 1
        self._reason(
            "NEW INPUT RECEIVED",
            "Jordan says: 'Actually, for urgent matters, please use Slack. "
            "Email is fine for non-urgent stuff, but if something is time-sensitive, "
            "Slack messages get my attention faster. Also, I'd like weekly summaries "
            "every Friday at 4 PM.'"
        )

        # Store the new preference -- this contradicts the Week 1 "email only" preference
        self._reason(
            "DETECTING CONTRADICTION",
            "Jordan previously said 'prefers email over Slack for non-urgent'. Now saying "
            "'prefers Slack for urgent matters'. This is NOT a full contradiction -- it's "
            "a refinement: email for non-urgent, Slack for urgent. Adding as a new "
            "preference with overlapping scope. The old preference remains valid for "
            "non-urgent communication."
        )

        await self.graphiti.add_episode(
            name="preference_slack_urgent",
            episode_body=(
                f"{self.user_name} prefers Slack for urgent/time-sensitive communication. "
                "For non-urgent matters, email is still preferred. This refines the "
                "earlier preference about email: email for routine, Slack for urgent."
            ),
            source="user_preference",
            source_description="Updated communication preference from Jordan",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Stored: preference_slack_urgent (refinement, not replacement)")

        # Store the weekly summary preference
        await self.graphiti.add_episode(
            name="preference_weekly_summary",
            episode_body=(
                f"{self.user_name} wants weekly summaries delivered every Friday at "
                "4 PM Eastern Time. The summary should cover completed tasks, "
                "pending items, and any important updates from the week."
            ),
            source="user_preference",
            source_description="Weekly summary schedule from Jordan",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Stored: preference_weekly_summary")

        # Let's also simulate a completely contradicted preference
        self._reason(
            "ADDING A FULLY CONTRADICTED PREFERENCE",
            "Jordan also says: 'Actually, I've changed my mind about dark mode. "
            "I now prefer the light theme -- I've gotten used to it.'"
        )
        self._reason(
            "CONTRADICTION DETECTED",
            "New preference 'light theme' contradicts 'dark mode' from Week 1. "
            "The OLD preference will be EXPIRED (marked with invalid_at), not deleted. "
            "This is important: expired preferences remain in the graph for history "
            "and audit trails, but they won't appear in current-preference queries."
        )

        await self.graphiti.add_episode(
            name="preference_light_theme",
            episode_body=(
                f"{self.user_name} now prefers the light theme in all applications. "
                f"{self.user_name} has changed from dark mode to light mode after "
                "getting used to the new UI. This supersedes the previous dark mode preference."
            ),
            source="user_preference",
            source_description="Updated theme preference from Jordan (contradicts Week 1)",
            reference_time=current_time,
            group_id=self.user_group_id,
        )
        print("    Stored: preference_light_theme (supersedes dark mode)")

        self._speak(
            "Got it! I'll use Slack for urgent matters and email for routine "
            "communication. I've also scheduled weekly summaries for Fridays at 4 PM. "
            "And I've updated your theme preference from dark mode to light mode -- "
            "don't worry, I still remember you preferred dark mode before, but I'll "
            "use light mode going forward."
        )

        # Query to show the assistant can still see both preferences
        self._reason(
            "VERIFYING MEMORY",
            "Checking that both old and new preferences are stored, but the old "
            "dark mode preference should be expired."
        )
        theme_memories = await self._query_memory("What theme does Jordan prefer?")
        self._print_memories(theme_memories, "THEME PREFERENCES (shows evolution)")

    # ==============================================================
    #  Week 3: User teaches a procedure
    # ==============================================================
    async def week_3_procedure_learning(self, current_time: datetime):
        """User teaches the assistant a multi-step procedure."""
        week_num = 3
        print("\n" + "=" * 72)
        print(f"WEEK {week_num}: User teaches a procedure")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        self._speak(
            "Hi Jordan! Ready for another week. What can I help you with?"
        )

        # User teaches the weekly report procedure
        self._reason(
            "PROCEDURE LEARNING IN PROGRESS",
            "Jordan is teaching a multi-step procedure: 'Let me show you how I "
            "prepare my weekly report. I want you to be able to do this for me.'"
        )

        # Store the procedure as episodes that capture each step
        procedure_steps = [
            (
                "procedure_weekly_report_step1",
                f"Step 1 of Jordan's weekly report procedure: Pull all completed "
                "tasks from the project management system (Jira). Filter for tasks "
                "with status 'Done' and resolution date in the current week."
            ),
            (
                "procedure_weekly_report_step2",
                f"Step 2 of Jordan's weekly report procedure: Categorize completed "
                "tasks into 'Engineering', 'Customer Support', and 'Internal' buckets. "
                "Engineering tasks go to the top of the report."
            ),
            (
                "procedure_weekly_report_step3",
                f"Step 3 of Jordan's weekly report procedure: For each task, include "
                "the ticket number, title, assignee, and a one-sentence summary of "
                "what was done. Do NOT include estimated vs actual time."
            ),
            (
                "procedure_weekly_report_step4",
                f"Step 4 of Jordan's weekly report procedure: Add a 'Blockers' section "
                "listing any tasks that were started but not completed, with the reason. "
                "Add a 'Next Week' section listing priorities for the coming week."
            ),
            (
                "procedure_weekly_report_step5",
                f"Step 5 of Jordan's weekly report procedure: Format the report as a "
                "Google Doc using the 'Weekly Report Template' in Jordan's drive. "
                "Share it with Jordan's manager (Sarah Chen) and the team lead "
                "(James Miller) with 'Comment' access. Send a Slack summary to Jordan."
            ),
        ]

        for name, body in procedure_steps:
            self._reason(f"LEARNING STEP: {name}", body[:100])
            await self.graphiti.add_episode(
                name=name,
                episode_body=body,
                source="user_procedure",
                source_description=f"Procedure taught by {self.user_name}",
                reference_time=current_time,
                group_id=self.user_group_id,
            )
            print(f"    Stored: {name}")

        self._speak(
            "I've learned the weekly report procedure! Here's what I'll do each week:\n"
            "  1. Pull completed tasks from Jira\n"
            "  2. Categorize into Engineering / Customer Support / Internal\n"
            "  3. Format with ticket details (no time estimates)\n"
            "  4. Add Blockers and Next Week sections\n"
            "  5. Create a Google Doc, share with Sarah and James, Slack you a summary\n"
            "I remember you like Slack summaries for urgent items -- this qualifies!"
        )

        # Verify procedure recall
        self._reason(
            "VERIFYING PROCEDURE RECALL",
            "Checking that I can recall the procedure steps correctly..."
        )
        procedure_memories = await self._query_memory(
            "What are the steps for the weekly report procedure?"
        )
        self._print_memories(procedure_memories, "PROCEDURE STEPS RECALLED")

    # ==============================================================
    #  Week 4: Assistant proactively helps
    # ==============================================================
    async def week_4_proactive_assistance(self, current_time: datetime):
        """Assistant uses accumulated knowledge to proactively help."""
        week_num = 4
        print("\n" + "=" * 72)
        print(f"WEEK {week_num}: Proactive assistance using accumulated knowledge")
        print(f"User: {self.user_name}")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 72)

        # The assistant proactively searches its memory before the user says anything
        self._reason(
            "ACTIVATING PROACTIVE MODE",
            "New week started. Let me check what I know about Jordan to see if "
            "there's anything I should proactively do or suggest..."
        )

        # Query multiple facets of knowledge
        all_knowledge = await self._query_memory(
            "What preferences, routines, and procedures does Jordan have?"
        )
        self._print_memories(all_knowledge, "COMPLETE KNOWLEDGE BASE (4 weeks)")

        self._reason(
            "TODAY IS FRIDAY -- CHECKING WEEKLY SUMMARY PREFERENCE",
            "Jordan wanted weekly summaries every Friday at 4 PM ET. Today is Friday! "
            "I should prepare the report proactively."
        )

        self._reason(
            "APPLYING LEARNED PREFERENCES",
            "Considerations for proactive outreach:\n"
            "  - It's within 9-5 ET work hours (respecting work hours preference)\n"
            "  - The weekly report is due today (Friday)\n"
            "  - Jordan prefers Slack for urgent/time-sensitive items\n"
            "  - The report should be shared with Sarah Chen and James Miller\n"
            "  - Use light theme when displaying information (updated preference)"
        )

        # Assistant proactively sends a message
        self._speak(
            "Good morning Jordan! Happy Friday! Here are a few things I've prepared "
            "based on what I've learned about you:\n"
            "\n"
            "1. WEEKLY REPORT: I've prepared your weekly report using the procedure "
            "you taught me. I pulled the completed tasks from Jira, categorized them, "
            "and created the Google Doc. Sarah Chen and James Miller have comment access.\n"
            "\n"
            "2. BLOCKERS: I noticed two tasks that were started but not completed -- "
            "the API rate limit fix (ENG-442) is waiting on a code review, and the "
            "customer onboarding doc (SUP-889) is pending input from Maria.\n"
            "\n"
            "3. NEXT WEEK PRIORITIES: Based on the sprint board, next week's focus "
            "should be the payment gateway integration and the Q2 performance review.\n"
            "\n"
            "I've sent a Slack summary as you requested. Have a great weekend! "
            "(I know you don't check messages on weekends, so I'll be quiet until Monday.)"
        )

        self._reason(
            "DEMONSTRATING KNOWLEDGE INTEGRATION",
            "The above response integrates knowledge from ALL 4 weeks:\n"
            "  - Week 1: Work hours (9-5 ET), light theme (was dark mode)\n"
            "  - Week 2: Slack for urgent, Friday 4 PM weekly summary\n"
            "  - Week 3: The full weekly report procedure (5 steps)\n"
            "  - All weeks: Jordan's name, manager, team structure\n"
            "  - Temporal awareness: 'weekends off' from Week 1"
        )

        # Final memory dump for verification
        print("\n  " + "-" * 60)
        print("  FINAL MEMORY AUDIT: What does the assistant know about Jordan?")
        print("  " + "-" * 60)

        audit_queries = [
            "What communication preferences does Jordan have?",
            "What are Jordan's work hours?",
            "What theme does Jordan prefer?",
            "What procedure did Jordan teach?",
            "When should the weekly summary be delivered?",
        ]

        for query in audit_queries:
            print(f'\n    Query: "{query}"')
            memories = await self._query_memory(query)
            self._print_memories(memories)

        # Show contradicted preference is expired, not deleted
        print("\n  " + "-" * 60)
        print("  CONTRADICTED PREFERENCE DEMONSTRATION")
        print("  " + "-" * 60)
        print(
            "\n"
            "  Key concept: When Jordan changed from dark mode to light mode in\n"
            "  Week 2, the dark mode preference was EXPIRED (marked invalid_at),\n"
            "  NOT DELETED. This means:\n"
            "\n"
            "  - Current-preference queries return light mode (the active one)\n"
            "  - Historical queries can still see dark mode was once preferred\n"
            "  - Full audit trail of preference changes is preserved\n"
            "  - If Jordan later says 'actually, I miss dark mode', the assistant\n"
            "    can recall the previous preference without re-learning it\n"
            "\n"
            "  This is the power of bi-temporal facts in a knowledge graph!\n"
        )


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 21: Personal Assistant with Preference Learning")
    print("=" * 72)
    print(
        "\n"
        "  This simulation follows an AI assistant learning about a user\n"
        "  over 4 weeks. The assistant uses Graphiti's temporal graph to:\n"
        "    - Remember preferences and routines\n"
        "    - Handle contradicted preferences (expire, not delete)\n"
        "    - Learn multi-step procedures\n"
        "    - Proactively apply accumulated knowledge\n"
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

    # Each user gets their own group_id
    user_group_id = "user_jordan_personal"

    # Create the assistant
    assistant = PersonalAssistant(graphiti, user_group_id)

    # Timeline: 4 weeks starting from 28 days ago
    # We set specific weekdays to make the Friday summary preference realistic
    base_time = datetime.now(timezone.utc) - timedelta(days=28)

    # Week 1: Monday
    week_1_time = base_time
    await assistant.week_1_preference_introduction(week_1_time)

    # Week 2: Monday
    week_2_time = base_time + timedelta(days=7)
    await assistant.week_2_preference_evolution(week_2_time)

    # Week 3: Monday
    week_3_time = base_time + timedelta(days=14)
    await assistant.week_3_procedure_learning(week_3_time)

    # Week 4: Friday (to trigger the weekly summary)
    week_4_time = base_time + timedelta(days=24)  # A Friday
    await assistant.week_4_proactive_assistance(week_4_time)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("SIMULATION SUMMARY")
    print("=" * 72)
    print(
        "\n"
        "  Over 4 weeks, the assistant learned and applied:\n"
        "\n"
        "  Week 1 - Initial Preferences:\n"
        "    - Dark mode preference (later contradicted in Week 2)\n"
        "    - Email for non-urgent communication\n"
        "    - Work hours 9-5 ET, no weekends\n"
        "\n"
        "  Week 2 - Preference Evolution:\n"
        "    - Added Slack for urgent communication (refinement)\n"
        "    - Changed dark mode to light mode (contradiction)\n"
        "    - Added Friday 4 PM weekly summary (new preference)\n"
        "    - OLD dark mode preference was EXPIRED, not deleted\n"
        "\n"
        "  Week 3 - Procedure Learning:\n"
        "    - Learned 5-step weekly report procedure\n"
        "    - Stored as structured episodes in the graph\n"
        "\n"
        "  Week 4 - Proactive Assistance:\n"
        "    - Recalled ALL knowledge across 4 weeks\n"
        "    - Prepared weekly report automatically\n"
        "    - Applied preferences (light theme, Slack summary)\n"
        "    - Respecting work hours (9-5) and weekends off\n"
        "\n"
        "  This is the foundation for AI assistants that truly learn\n"
        "  and adapt to individual users over time!\n"
    )

    # -- Cleanup ------------------------------------------------------------
    await graphiti.close()
    print("\nDone. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
