"""
Example 24: Codebase Evolution Tracking

This example simulates tracking a software project's API surface across three
major releases (v1.0, v2.0, v3.0). It demonstrates how Graphiti can model:

  1. Custom entities: Module, Class, Function, API
  2. Custom relationships: depends_on, calls, deprecated_in, replaced_by,
     introduced_in
  3. Temporal validity: when was each API valid?
  4. Deprecation tracking: old APIs are expired (invalid_at), not deleted
  5. Dependency analysis: what depends on what
  6. Refactoring history: what replaced what and when

The fictional project is "PyAuth" -- an authentication library for Python web apps.
"""

import asyncio
import os
import sys

from datetime import datetime, timezone, timedelta
from textwrap import dedent

# ---------------------------------------------------------------------------
# Environment / connectivity check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux/Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    import socket

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


def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges with temporal metadata."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] fact:     {e.fact}")
        print(f"      source:   {e.source_node_name} --> {e.target_node_name}")
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if e.invalid_at:
            print(f"      expired:  {e.invalid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


# ===================================================================
# Simulation
# ===================================================================
async def simulate_code_evolution():
    """Add episodes representing three releases of PyAuth."""
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    group_id = "pyauth_codebase"
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    # ===================================================================
    # v1.0 -- Initial Release (January 2024)
    # ===================================================================
    print("\n" + "=" * 72)
    print("RELEASE v1.0 -- Initial API Surface (Jan 2024)")
    print("=" * 72)

    v1_time = base_time

    await graphiti.add_episode(
        name="v1_pyauth_module",
        episode_body=dedent("""
            Module: pyauth (v1.0.0)

            The pyauth module provides authentication and authorization
            functionality for Python web frameworks.

            Classes:
            - AuthManager: Core authentication manager. Handles user login,
              logout, and session management. Uses bcrypt for password hashing.
              Introduced in v1.0.

            - PermissionChecker: Evaluates user permissions against resources.
              Uses role-based access control (RBAC). Introduced in v1.0.

            - TokenGenerator: Generates and validates JWT tokens.
              Supports HS256 and RS256 signing algorithms. Introduced in v1.0.

            Functions:
            - authenticate_v1(username, password): Validates credentials
              against the user store. Returns a session token on success.
              Introduced in v1.0.

            - hash_password_v1(password): Hashes a password using bcrypt
              with cost factor 12. Returns the hashed string.
              Introduced in v1.0.

            - validate_token_v1(token): Validates a JWT token and returns
              the decoded payload. Raises TokenExpiredError if expired.
              Introduced in v1.0.
        """),
        source=EpisodeType.text,
        source_description="API reference documentation",
        reference_time=v1_time,
        group_id=group_id,
    )
    print("  [v1.0] Added: pyauth module with 3 classes and 3 functions")

    await graphiti.add_episode(
        name="v1_module_dependencies",
        episode_body=dedent("""
            The pyauth module depends_on the following external packages:
            - bcrypt (password hashing)
            - PyJWT (JWT token handling)
            - cryptography (for RS256 signing)

            Internal dependencies:
            - AuthManager depends_on TokenGenerator for creating session tokens
            - AuthManager depends_on PermissionChecker for authorization checks
            - PermissionChecker depends_on TokenGenerator for token validation
            - authenticate_v1 calls AuthManager.authenticate()
            - validate_token_v1 calls TokenGenerator.validate()
        """),
        source=EpisodeType.text,
        source_description="Dependency documentation",
        reference_time=v1_time,
        group_id=group_id,
    )
    print("  [v1.0] Added: Internal and external dependency graph")

    # ===================================================================
    # v2.0 -- Deprecations + New Features (June 2024)
    # ===================================================================
    print("\n" + "=" * 72)
    print("RELEASE v2.0 -- Deprecations & New Features (Jun 2024)")
    print("=" * 72)

    v2_time = v1_time + timedelta(days=180)

    await graphiti.add_episode(
        name="v2_deprecations",
        episode_body=dedent("""
            PyAuth v2.0.0 deprecates the following APIs:

            - authenticate_v1(): Deprecated. Use authenticate_v2() instead.
              The old function has a rigid interface that doesn't support
              MFA tokens. Deprecated in v2.0, will be removed in v3.0.

            - hash_password_v1(): Deprecated. Use hash_password_v2() instead.
              The new function supports argon2 and bcrypt algorithms.
              Deprecated in v2.0, will be removed in v3.0.

            - validate_token_v1(): Deprecated. Use validate_token_v2() instead.
              The new function supports additional token types (API keys,
              service tokens). Deprecated in v2.0, will be removed in v3.0.
        """),
        source=EpisodeType.text,
        source_description="Migration guide",
        reference_time=v2_time,
        group_id=group_id,
    )
    print("  [v2.0] Added: Deprecation notices for 3 functions")

    await graphiti.add_episode(
        name="v2_new_apis",
        episode_body=dedent("""
            PyAuth v2.0.0 introduces the following new APIs:

            Functions:
            - authenticate_v2(username, password, mfa_code=None): Enhanced
              authentication with optional MFA support. Returns a session token.
              Introduced in v2.0.

            - hash_password_v2(password, algorithm='bcrypt'): Password hashing
              supporting bcrypt (default) or argon2 algorithms. Returns a
              hash string with algorithm prefix. Introduced in v2.0.

            - validate_token_v2(token, token_type='jwt'): Token validation
              supporting JWT, API key, and service token types.
              Introduced in v2.0.

            Classes:
            - MFAManager: Handles multi-factor authentication setup and
              verification. Supports TOTP (Google Authenticator) and SMS.
              Introduced in v2.0.

            The AuthManager class has been updated:
            - AuthManager now supports MFA via MFAManager
            - AuthManager.authenticate() calls authenticate_v2 internally
        """),
        source=EpisodeType.text,
        source_description="API reference documentation",
        reference_time=v2_time,
        group_id=group_id,
    )
    print("  [v2.0] Added: 3 new functions and MFAManager class")

    await graphiti.add_episode(
        name="v2_dependency_changes",
        episode_body=dedent("""
            New external dependencies in v2.0:
            - pyotp (for TOTP generation in MFA)
            - argon2-cffi (for argon2 password hashing support)

            Updated dependencies:
            - bcrypt dependency remains
            - PyJWT dependency remains
            - cryptography dependency remains

            Internal dependency changes in v2.0:
            - authenticate_v2 replaces authenticate_v1 as the primary auth entry point
            - hash_password_v2 replaces hash_password_v1 for password hashing
            - validate_token_v2 replaces validate_token_v1 for token validation
            - AuthManager now depends_on MFAManager for MFA support
        """),
        source=EpisodeType.text,
        source_description="Changelog",
        reference_time=v2_time,
        group_id=group_id,
    )
    print("  [v2.0] Added: New external and internal dependencies")

    # ===================================================================
    # v3.0 -- Major Refactor (January 2025)
    # ===================================================================
    print("\n" + "=" * 72)
    print("RELEASE v3.0 -- Major Refactor (Jan 2025)")
    print("=" * 72)

    v3_time = v2_time + timedelta(days=210)

    await graphiti.add_episode(
        name="v3_removals",
        episode_body=dedent("""
            PyAuth v3.0.0 removes deprecated APIs:

            Removed (as announced in v2.0):
            - authenticate_v1(): Removed. Use authenticate_v2().
            - hash_password_v1(): Removed. Use hash_password_v2().
            - validate_token_v1(): Removed. Use validate_token_v2().

            These functions were deprecated in v2.0 and are now removed.
            Any code still using them will break.

            Additionally, the following are newly deprecated in v3.0:
            - PermissionChecker class: Deprecated. Use the new AuthorizationManager
              class instead. Deprecated in v3.0, will be removed in v4.0.
            - TokenGenerator class: Deprecated. Token generation is now handled
              by the new AuthService facade. Deprecated in v3.0, will be removed
              in v4.0.
        """),
        source=EpisodeType.text,
        source_description="Breaking changes documentation",
        reference_time=v3_time,
        group_id=group_id,
    )
    print("  [v3.0] Added: Removal of 3 deprecated functions, new deprecations")

    await graphiti.add_episode(
        name="v3_new_architecture",
        episode_body=dedent("""
            PyAuth v3.0.0 introduces a completely refactored architecture:

            New Classes:
            - AuthService: Unified facade for all authentication operations.
              Replaces the direct use of AuthManager + TokenGenerator.
              Provides authenticate(), validate(), refresh(), and revoke().
              Introduced in v3.0.

            - AuthorizationManager: Replaces PermissionChecker.
              Supports RBAC and ABAC (attribute-based access control).
              Introduced in v3.0.

            - SessionStore: Manages session persistence with Redis backend.
              Supports session revocation and TTL-based expiration.
              Introduced in v3.0.

            - AuditLogger: Logs all authentication events for compliance.
              Supports structured JSON logging. Introduced in v3.0.

            Updated Classes:
            - AuthManager: Refactored to delegate to AuthService internally.
              The public API is unchanged for backward compatibility.

            New Functions:
            - create_api_key(): Generates scoped API keys for service-to-service
              authentication. Introduced in v3.0.

            Architecture changes:
            - The pyauth module no longer depends_on TokenGenerator directly.
            - AuthService replaces TokenGenerator + AuthManager for new code.
            - SessionStore replaces in-memory session management.
        """),
        source=EpisodeType.text,
        source_description="Architecture documentation",
        reference_time=v3_time,
        group_id=group_id,
    )
    print("  [v3.0] Added: Refactored architecture with 4 new classes")

    await graphiti.add_episode(
        name="v3_dependency_rewiring",
        episode_body=dedent("""
            v3.0 dependency restructuring:

            Removed external dependencies:
            - PyJWT: No longer needed (replaced by python-jose)
            - cryptography: No longer needed (replaced by python-jose)

            New external dependencies:
            - python-jose (unified JOSE library replacing PyJWT + cryptography)
            - redis (for SessionStore backend)
            - structlog (for AuditLogger structured logging)

            Kept external dependencies:
            - bcrypt (still used for password hashing)
            - pyotp (still used for MFA)
            - argon2-cffi (still used for argon2 hashing)

            New internal dependencies:
            - AuthService depends_on SessionStore for session persistence
            - AuthService depends_on AuditLogger for event logging
            - AuthorizationManager depends_on AuditLogger for access log
            - AuthorizationManager depends_on SessionStore for role caching
            - AuthService replaced_by TokenGenerator (TokenGenerator is deprecated)
            - AuthorizationManager replaced_by PermissionChecker (PermissionChecker deprecated)
        """),
        source=EpisodeType.text,
        source_description="Dependency changelog",
        reference_time=v3_time,
        group_id=group_id,
    )
    print("  [v3.0] Added: Updated external dependencies and internal rewiring")

    return graphiti, group_id


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 24: Codebase Evolution Tracking")
    print("Tracking PyAuth library across v1.0 -> v2.0 -> v3.0")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    graphiti, group_id = await simulate_code_evolution()

    # ==================================================================
    # Query 1: What APIs were available in v2.0?
    # ==================================================================
    print("\n" + "=" * 72)
    print("QUERY 1: What APIs were available in v2.0?")
    print("=" * 72)
    print(
        "  v2.0 had the deprecated v1 APIs (still valid) plus the new v2 APIs.\n"
        "  This query should surface both sets.\n"
    )
    edges = await graphiti.search(
        query="What APIs, classes, and functions were available in PyAuth v2.0?",
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} APIs available in v2.0")

    # ==================================================================
    # Query 2: What replaced authenticate_v1()?
    # ==================================================================
    print("\n" + "=" * 72)
    print("QUERY 2: What replaced authenticate_v1()?")
    print("=" * 72)
    print(
        "  authenticate_v1 was deprecated in v2.0 and removed in v3.0.\n"
        "  Its replacement is authenticate_v2(). This demonstrates how\n"
        "  replaced_by relationships bridge old and new APIs.\n"
    )
    edges = await graphiti.search(
        query="What replaced the authenticate_v1 function in PyAuth? What is the migration path?",
        group_ids=[group_id],
        num_results=5,
    )
    print_edges(edges, f"Found {len(edges)} relationships for authenticate_v1 replacement")

    # ==================================================================
    # Query 3: What depends on the auth module?
    # ==================================================================
    print("\n" + "=" * 72)
    print("QUERY 3: What depends on the payment module?")
    print("=" * 72)
    print(
        "  This demonstrates dependency analysis. In our case, we'll ask about\n"
        "  PyAuth's internal and external dependencies.\n"
    )
    edges = await graphiti.search(
        query=(
            "What are the internal and external dependencies of the pyauth module? "
            "Which classes and functions depend on each other?"
        ),
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} dependency relationships")

    # ==================================================================
    # Query 4: Deprecation history across versions
    # ==================================================================
    print("\n" + "=" * 72)
    print("QUERY 4: Full deprecation and removal history")
    print("=" * 72)
    print(
        "  Shows all APIs that were deprecated or removed across versions.\n"
        "  This illustrates how Graphiti preserves deprecation information.\n"
    )
    edges = await graphiti.search(
        query=(
            "What APIs were deprecated or removed across PyAuth versions? "
            "Show the deprecation timeline."
        ),
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} deprecation/removal records")

    # ==================================================================
    # Query 5: What changed between v1.0 and v3.0?
    # ==================================================================
    print("\n" + "=" * 72)
    print("QUERY 5: How did the architecture evolve from v1.0 to v3.0?")
    print("=" * 72)
    print(
        "  This demonstrates the full evolution story: from a simple 3-class\n"
        "  design in v1.0 to a comprehensive architecture with service facades,\n"
        "  session management, and audit logging in v3.0.\n"
    )
    edges = await graphiti.search(
        query=(
            "How did the PyAuth architecture evolve from v1.0 to v3.0? "
            "What classes were added, removed, or refactored?"
        ),
        group_ids=[group_id],
        num_results=15,
    )
    print_edges(edges, f"Found {len(edges)} architecture evolution records")

    # ==================================================================
    # Temporal validity deep-dive
    # ==================================================================
    print("\n" + "=" * 72)
    print("TEMPORAL VALIDITY DEEP-DIVE")
    print("=" * 72)
    print(
        "  In Graphiti, deprecated/removed APIs are NOT deleted. Their edges\n"
        "  simply get an invalid_at timestamp. This means:\n\n"
        "  - Querying without time filter returns ALL facts (current + historical)\n"
        "  - Querying with a time-bound filter returns only facts valid at that time\n"
        "  - The full history is always preserved for audit and rollback\n\n"
        "  This is critical for codebase evolution because:\n"
        "    - You can ask 'what was the API in v1.0?' and get an accurate answer\n"
        "    - You can trace exactly when each deprecation happened\n"
        "    - Breaking changes are documented in the graph, not lost in git history\n"
    )

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 72)
    print("Key Takeaways")
    print("=" * 72)
    print("""
  1. Custom entities
     Graphiti extracts Module, Class, Function, and API entities from
     structured documentation.

  2. Deprecation tracking
     deprecated_in and replaced_by edges capture the lifecycle of each API.
     Old edges are expired (invalid_at), not deleted.

  3. Temporal validity
     Each API's validity period is captured. You can reconstruct the exact
     API surface for any release version.

  4. Dependency analysis
     depends_on edges build a complete dependency graph. Queries can surface
     transitive dependencies and impact analysis.

  5. Refactoring history
     replaced_by edges trace the full refactoring history, showing exactly
     what replaced what and when.
""")

    # Clean up
    print("\nCleaning up...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
