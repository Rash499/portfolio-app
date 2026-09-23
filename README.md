# Interactive System Architecture Portfolio

A portfolio builder for DevOps/Cloud/SRE/Platform engineers. Instead of a wall of
text, each project is presented as a **real, clickable architecture diagram** —
built with React Flow — where every node (service, database, Kubernetes cluster,
CI pipeline, GitOps repo, security control, monitoring stack, ...) opens a detail
panel with real data pulled from a real database through a real API.

Built entirely on free/open-source technology: **FastAPI, PostgreSQL, SQLAlchemy,
React, TypeScript, Vite, Tailwind, React Flow, Docker.**

---

## 1. What's actually implemented (read this first)

This is a real, working, tested application — not a mockup. What's included:

- **Auth**: register / login / refresh / logout / me, JWT access + refresh tokens,
  bcrypt password hashing, protected routes, ownership checks.
- **Portfolios**: full CRUD, public/private visibility, public slug URLs (`/p/<slug>`).
- **Projects**: full CRUD per portfolio, status, technologies, links, publish/unpublish.
- **Interactive architecture editor**: add/edit/delete/drag nodes, connect/delete
  edges, ~38 node types (frontend, backend, database, Kubernetes, CI pipeline, GitOps
  repository, Argo CD/Flux CD controller, security, monitoring, etc.), a flexible
  JSON metadata field per node so CI stages, GitOps sync info, security controls,
  dependencies, endpoints, or anything else can be attached to any node type.
- **Public architecture viewer**: read-only interactive diagram, click a node → see
  its full detail panel. This is the core differentiator from the spec.
- **Architecture as code**: every diagram exports as a lossless **JSON bundle**
  (nodes, edges, metadata, canvas positions) or as **Mermaid** source that renders
  in GitHub READMEs, Notion or mermaid.live — and imports back either way, in
  `merge` or `replace` mode, so diagrams can be pasted between projects, generated
  by a script, or committed next to the code. Public/published projects expose the
  Mermaid export to anonymous visitors (a "View as Mermaid" button on the project
  page); importing always requires ownership.
- **API Explorer**: per-project endpoint documentation (method, path, description,
  auth requirement, status codes), filterable by HTTP method.
- **Global search** across public portfolios, projects, skills, and architecture nodes.
- **Docker Compose** stack (Postgres + FastAPI + React), with health checks.
- **Automated tests**: 31 backend tests (pytest) covering auth, ownership,
  portfolio/project/architecture CRUD, public visibility rules, search, and
  diagram export/import round-trips — **plus 11 frontend tests (vitest) for the
  diagram export helpers**. Frontend type-checks and builds cleanly.
- **GitHub Actions CI**: backend lint (Ruff) + security scan (Bandit) + tests +
  coverage, frontend type-check + build, Docker image builds, Trivy filesystem scan.

### What was intentionally scoped down (be aware of this before you demo it as "everything")

The original spec asked for an enterprise-scale platform (dozens of normalized
tables for every sub-entity, full Alembic migration history, a live Argo CD/Flux
integration, a Playwright E2E suite, 80%/70% enforced coverage, role grouping,
node duplication/search-within-canvas, environment-promotion workflows, rollback
visualizations, etc). Building all of that to production quality is a multi-week
project. To keep this genuinely working rather than half-real, I made these
deliberate trade-offs:

- **Schema**: CI/CD, GitOps, security, monitoring, and infrastructure detail live
  in a flexible `metadata_json` field on `architecture_nodes` rather than as ~15
  separate normalized tables. You can still model an Argo CD controller node with
  `{"repo": "...", "sync": "automatic", "target_cluster": "..."}` etc. — it's just
  schema-flexible instead of schema-rigid.
- **Migrations**: the backend uses `SQLAlchemy.metadata.create_all()` on startup
  instead of Alembic. This is fine for getting started; see `docs/database.md` for
  how to add real Alembic migrations before you rely on this in production.
- **No Playwright E2E suite** — backend tests cover the same user flows at the API
  level instead (see `backend/tests/`).
- **No live GitOps controller integration** — GitOps/Argo CD/Flux nodes are
  *documented*, not *connected to* a real cluster.
- **UI is functional, not pixel-polished** — dark theme, responsive-ish, but no
  custom illustration or animation pass.

None of this is hidden or faked — it's a real Postgres-backed CRUD app you can run
right now.

---

## 2. Project structure

```text
portfolio-app/
├── docker-compose.yml
├── .env.example
├── backend/            FastAPI app (see backend/app/)
│   ├── app/
│   │   ├── main.py, config.py, database.py, models.py, schemas.py
│   │   ├── security.py, deps.py
│   │   ├── diagram_io.py   JSON/Mermaid export + import codec
│   │   └── routers/    auth, portfolios, projects, architecture, search
│   └── tests/          pytest suite
├── frontend/           React + TypeScript + Vite app
│   └── src/
│       ├── pages/       Login, Register, Dashboard, PortfolioEditor,
│       │                ProjectEditor, ArchitectureEditor (React Flow editor),
│       │                PublicPortfolio, PublicProject (read-only diagram viewer),
│       │                SearchPage
│       ├── components/  NavBar, ProtectedRoute, NodeDetailPanel,
│       │                MermaidPanel, DiagramImportPanel
│       ├── utils/       diagramTransfer (filename/download/clipboard helpers)
│       ├── store/       auth (zustand)
│       └── api/         axios client with automatic token refresh
└── .github/workflows/ci.yml
```

---

## 3. Run it locally with Docker (recommended)

Requires Docker + Docker Compose.

```bash
cd portfolio-app
cp .env.example .env          # edit JWT secrets if you want
docker compose up --build
```

This starts three services:

- `postgres` on `localhost:5432`
- `backend` (FastAPI) on `localhost:8000` — API docs at `http://localhost:8000/docs`
- `frontend` (built React app served by `serve`) on `localhost:4173`

Open **http://localhost:4173**, register an account, create a portfolio, create a
project, open its architecture editor, add a few nodes, connect them, publish the
project and the portfolio, then visit `http://localhost:4173/p/<your-slug>`.

To stop: `docker compose down` (add `-v` to also wipe the Postgres volume).

---

## 4. Run it locally without Docker (faster iteration)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# quickest: run against SQLite instead of Postgres for local dev
export DATABASE_URL=sqlite:///./dev.db
export JWT_SECRET=dev-secret
export JWT_REFRESH_SECRET=dev-refresh-secret
uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a second terminal):

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Open **http://localhost:5173**.

**Run the backend tests:**

```bash
cd backend
DATABASE_URL=sqlite:///:memory: pytest --cov=app --cov-report=term-missing
```

**Run the frontend tests:**

```bash
cd frontend
npm run test
```

### Exporting a diagram as Mermaid or JSON (architecture as code)

Open a project's architecture editor and use the toolbar:

- **Mermaid** — shows the chart as Mermaid source with *Copy code*, *Copy README
  block* (a fenced ```` ```mermaid ```` snippet), *Download .mmd* and a link to
  mermaid.live. Node types become Mermaid shapes (databases become cylinders, CI
  jobs subroutines, clusters hexagons, …) plus a `[type]` label suffix, and the
  chart ends with `classDef` colouring per component family.
- **Export JSON** — downloads the lossless bundle
  (`<portfolio>-<project>-architecture.json`) with every field, including
  `metadata_json` and canvas coordinates.
- **Import** — paste or upload either format and pick `Merge` (append to the
  current diagram) or `Replace` (clear it first). Imported Mermaid is auto-laid
  out on a grid, because Mermaid code has no coordinates.

Any published project inside a public portfolio also exposes the Mermaid export
on its public page (**View as Mermaid**), which is how you get a README-ready
diagram out of a portfolio without logging in.

```bash
# Same thing over the API:
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/projects/$PROJECT_ID/export/mermaid

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/projects/$PROJECT_ID/export/json \
  > architecture.json

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data @architecture.json "http://localhost:8000/api/projects/$PROJECT_ID/import?mode=replace"
```

---

## 5. Deploying for free

Every piece of this stack has a free tier:

| Component | Free option |
|---|---|
| Postgres | [Neon](https://neon.tech) or [Supabase](https://supabase.com) free tier — copy the connection string into `DATABASE_URL` |
| Backend (FastAPI/Docker) | [Render](https://render.com) free web service, or [Fly.io](https://fly.io) free allowance — both build straight from `backend/Dockerfile` |
| Frontend (static/Docker) | [Render](https://render.com) static site or free web service from `frontend/Dockerfile`, or [Netlify](https://netlify.com)/[Vercel](https://vercel.com) for `frontend/dist` after `npm run build` |
| CI | GitHub Actions — free for public repos, generous free minutes for private ones |

General steps:

1. Push this repo to GitHub.
2. Create a free Postgres database (Neon/Supabase), copy its connection string.
3. Deploy `backend/` as a Docker web service on Render/Fly, setting env vars
   `DATABASE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `CORS_ORIGINS` (your
   frontend's URL).
4. Deploy `frontend/` the same way, setting `VITE_API_URL` (build arg) to your
   backend's public URL.
5. Visit your frontend URL — same flow as local: register → create portfolio →
   create project → build architecture → publish.

---

## 6. API reference

Once the backend is running, full interactive docs are at:

- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

Key endpoints:

```text
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/portfolios/me
POST   /api/portfolios
GET    /api/portfolios/{id}
PUT    /api/portfolios/{id}
DELETE /api/portfolios/{id}
GET    /api/portfolios/public/{slug}
GET    /api/portfolios/public/{slug}/projects

POST   /api/projects/portfolio/{portfolio_id}
GET    /api/projects/portfolio/{portfolio_id}
GET    /api/projects/{id}
PUT    /api/projects/{id}
DELETE /api/projects/{id}
GET    /api/projects/public/{portfolio_slug}/{project_slug}

POST   /api/projects/{project_id}/nodes
PUT    /api/nodes/{node_id}
DELETE /api/nodes/{node_id}
POST   /api/projects/{project_id}/edges
DELETE /api/edges/{edge_id}
GET    /api/projects/{project_id}/diagram

POST   /api/projects/{project_id}/endpoints
GET    /api/projects/{project_id}/endpoints
DELETE /api/endpoints/{endpoint_id}

GET    /api/projects/{project_id}/export/json      # lossless JSON bundle (owner or public project)
GET    /api/projects/{project_id}/export/mermaid   # Mermaid flowchart source (owner or public project)
POST   /api/projects/{project_id}/import           # JSON bundle, ?mode=merge|replace (owner only)
POST   /api/projects/{project_id}/import/mermaid   # Mermaid source, ?mode=merge|replace (owner only)

GET    /api/search?q=...
```

---

## 7. Known limitations

- No Alembic migrations yet (uses `create_all()` — fine for dev/small deployments,
  not for zero-downtime schema changes at scale).
- No rate limiting, audit log table, or CSRF handling (JWT bearer tokens in
  `Authorization` headers sidestep CSRF, but there's no audit trail yet).
- No file/image upload (profile pictures, resumes) — add an object-storage
  integration (MinIO locally, S3-compatible in prod) if you need this.
- No Playwright E2E suite; no live GitOps controller connection.
- Search is a simple substring scan over public records, not a full-text index —
  fine at small scale, would want Postgres full-text search or similar at scale.
- Diagram **import** from Mermaid understands the subset the exporter emits (node
  definitions with shapes/labels, `-->`, `-->|label|`, `-- label -->` arrows,
  `%%` comments, `classDef`/`class`/`style` lines, and `subgraph` blocks are
  accepted but flattened). Exotic Mermaid syntax (`&` fan-out, `o--o`/`x--x`
  links, `linkStyle` styling) is rejected with a line number rather than
  silently mis-parsed. Mermaid is also lossy by design: `metadata_json`,
  versions, environments and canvas coordinates only survive in the JSON bundle.
