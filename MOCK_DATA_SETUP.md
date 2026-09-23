Mock data

This folder contains realistic demo data for the Interactive System Architecture Portfolio.

Files

mock_data.json — editable portfolio/project/node/edge/API data.

seed_mock_data.py — idempotent SQLAlchemy seeder.

__init__.py — makes seed runnable as a Python module.

Run locally

From the backend directory:

python -m seed.seed_mock_data

Make sure your PostgreSQL database is running and DATABASE_URL points to it.

Run with Docker Compose

From the project root:

docker compose up -d postgres backend
docker compose exec backend python -m seed.seed_mock_data

Then start the frontend and open:

http://localhost:5173/p/demo-architect

Demo account:

Email: demo@architecture.dev
Password: Demo123!

The seed is safe to run repeatedly. It updates the demo portfolio and replaces the demo projects' nodes, edges, and API endpoint data so the mock architecture stays deterministic.

The demo data is intentionally fictional. Replace the example GitHub, LinkedIn, website, and project URLs before publishing the portfolio.