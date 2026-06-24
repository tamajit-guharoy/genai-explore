# ─── Migrate from Flask to FastAPI ───

openhands --headless --override-with-envs \
  -t "Migrate this Flask application to FastAPI:

       1. Convert Flask routes to FastAPI path operations
       2. Replace Flask request objects with FastAPI dependency injection
       3. Convert Flask-SQLAlchemy to SQLAlchemy 2.0 async
       4. Replace Flask-JWT with python-jose + passlib
       5. Add Pydantic models for all request/response schemas
       6. Update tests from pytest-flask to httpx TestClient
       7. Add type hints to all functions

       Rules:
       - Preserve ALL existing behavior — this is a refactor, not a rewrite
       - Keep the same URL paths where possible
       - All existing tests must pass (updated for FastAPI)
       - Add migration notes to MIGRATION.md"

# ─── After migration ───
pytest && echo "✓ Migration complete, all tests pass"
cat MIGRATION.md