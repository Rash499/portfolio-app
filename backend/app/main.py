from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 ensures models are registered before create_all
from app.routers import auth, portfolios, projects, architecture, search

app = FastAPI(
    title="Interactive System Architecture Portfolio API",
    description="Backend API for building interactive, clickable system-architecture portfolios.",
    version="0.1.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Using create_all for a fast, dependency-light bootstrap. For a production
    # deployment, swap this for real Alembic migrations (see docs/database.md).
    Base.metadata.create_all(bind=engine)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(projects.router)
app.include_router(architecture.router)
app.include_router(search.router)
