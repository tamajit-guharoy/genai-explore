mkdir my-fastapi-app && cd my-fastapi-app

openhands --headless --override-with-envs \
  -t "Create a production-ready FastAPI application:

       Features:
       - REST API for a task management app (CRUD: tasks, users)
       - PostgreSQL with SQLAlchemy async
       - Alembic for migrations
       - Pydantic v2 for validation
       - JWT authentication (access + refresh tokens)
       - Rate limiting (slowapi)
       - Structured logging (structlog)
       - Health check endpoint
       - OpenAPI docs at /docs

       Project structure:
       app/
         main.py          — FastAPI app factory
         config.py        — Settings from env vars
         models/          — SQLAlchemy models
         schemas/         — Pydantic schemas
         api/v1/          — Route handlers
         core/            — Auth, deps, security
       tests/
       alembic/
       Dockerfile
       docker-compose.yml
       README.md

       Write ALL files with full implementations.
       Include docstrings and type hints throughout.
       Run the tests to verify: pytest -v"