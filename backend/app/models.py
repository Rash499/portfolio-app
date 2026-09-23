import uuid
import datetime as dt

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, Integer, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR

from app.database import Base


class GUID(TypeDecorator):
    """Platform-independent UUID type: Postgres UUID, else CHAR(36) (so tests can use SQLite)."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    owner_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    professional_title = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    skills = Column(JSON, default=list)
    github_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_public = Column(Boolean, default=False)
    theme = Column(String(50), default="dark")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    owner = relationship("User", back_populates="portfolios")
    projects = relationship("Project", back_populates="portfolio", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    portfolio_id = Column(GUID(), ForeignKey("portfolios.id"), nullable=False)
    slug = Column(String(150), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    short_description = Column(String(500), nullable=True)
    full_description = Column(Text, nullable=True)
    status = Column(String(50), default="development")  # planning/development/completed/maintenance/archived
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    technologies = Column(JSON, default=list)
    github_url = Column(String(500), nullable=True)
    live_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    key_features = Column(JSON, default=list)
    challenges = Column(Text, nullable=True)
    solutions = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    __table_args__ = (UniqueConstraint("portfolio_id", "slug", name="uq_project_slug_per_portfolio"),)

    portfolio = relationship("Portfolio", back_populates="projects")
    nodes = relationship("ArchitectureNode", back_populates="project", cascade="all, delete-orphan")
    edges = relationship("ArchitectureEdge", back_populates="project", cascade="all, delete-orphan")
    endpoints = relationship("ApiEndpoint", back_populates="project", cascade="all, delete-orphan")


class ArchitectureNode(Base):
    """
    A generic architecture component. `node_type` selects the visual/semantic category
    (frontend, backend, database, kubernetes, ci_pipeline, gitops_repository,
    gitops_controller, security, monitoring, etc). `metadata_json` holds the
    type-specific detail fields (technology, version, endpoints summary, CI stages,
    GitOps sync info, security controls, monitoring tools, dependencies, ...) so that
    the ~40 node types in the spec don't require ~40 separate tables.
    """
    __tablename__ = "architecture_nodes"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    node_type = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technology = Column(String(150), nullable=True)
    version = Column(String(50), nullable=True)
    environment = Column(String(50), nullable=True)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    project = relationship("Project", back_populates="nodes")


class ArchitectureEdge(Base):
    __tablename__ = "architecture_edges"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    source_node_id = Column(GUID(), ForeignKey("architecture_nodes.id"), nullable=False)
    target_node_id = Column(GUID(), ForeignKey("architecture_nodes.id"), nullable=False)
    label = Column(String(255), nullable=True)

    project = relationship("Project", back_populates="edges")


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"
    id = Column(GUID(), primary_key=True, default=gen_uuid)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    method = Column(String(10), nullable=False)  # GET/POST/PUT/PATCH/DELETE
    path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    requires_auth = Column(Boolean, default=False)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    status_codes = Column(JSON, default=list)

    project = relationship("Project", back_populates="endpoints")
