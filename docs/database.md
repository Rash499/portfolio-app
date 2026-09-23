# Database notes

## Current approach

The backend currently calls `Base.metadata.create_all(bind=engine)` on startup
(see `app/main.py`). This creates all tables directly from the SQLAlchemy models
in `app/models.py` if they don't already exist. It's simple and has zero extra
dependencies, which is why it's the default here — but it does **not** track
schema history and cannot express an "alter column" migration; it only ever
adds missing tables.

## Adding real Alembic migrations

For a production deployment where you'll evolve the schema over time, swap to
Alembic:

```bash
cd backend
pip install alembic
alembic init alembic
```

In the generated `alembic/env.py`, point `target_metadata` at the app's models:

```python
from app.database import Base
from app import models  # noqa: F401 — ensures models are imported/registered
target_metadata = Base.metadata
```

And set `sqlalchemy.url` in `alembic.ini` (or read it from `app.config.settings`
inside `env.py`) to your `DATABASE_URL`.

Generate the first migration from the current models:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Then remove the `Base.metadata.create_all(...)` call in `app/main.py`'s startup
event and run `alembic upgrade head` as a deploy step instead (e.g. in the
Docker `CMD`, or as a separate CI/CD step before the app container starts).

## Schema overview

- `users` — auth
- `portfolios` — one owner, many projects, public/private via `is_public`
- `projects` — belong to a portfolio, publish state via `is_published`
- `architecture_nodes` — generic component nodes; `node_type` selects the
  category (frontend/backend/database/kubernetes/ci_pipeline/gitops_repository/
  argo_cd/security/monitoring/...); `metadata_json` holds type-specific detail
  (CI stages, GitOps sync config, security controls, dependencies, etc.) so the
  ~38 node types from the spec don't require ~38 separate tables
- `architecture_edges` — directed connections between nodes
- `api_endpoints` — per-project documented API routes (the "API Explorer")
