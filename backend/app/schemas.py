import datetime as dt
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    created_at: dt.datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Portfolio ----------
class PortfolioBase(BaseModel):
    slug: str = Field(min_length=3, max_length=150, pattern=r"^[a-z0-9-]+$")
    title: str
    professional_title: Optional[str] = None
    about: Optional[str] = None
    skills: List[str] = []
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    is_public: bool = False
    theme: str = "dark"


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    title: Optional[str] = None
    professional_title: Optional[str] = None
    about: Optional[str] = None
    skills: Optional[List[str]] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    is_public: Optional[bool] = None
    theme: Optional[str] = None


class PortfolioOut(PortfolioBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    created_at: dt.datetime
    updated_at: dt.datetime


# ---------- Project ----------
class ProjectBase(BaseModel):
    slug: str = Field(min_length=2, max_length=150, pattern=r"^[a-z0-9-]+$")
    name: str
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    status: str = "development"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technologies: List[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    documentation_url: Optional[str] = None
    key_features: List[str] = []
    challenges: Optional[str] = None
    solutions: Optional[str] = None
    is_published: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technologies: Optional[List[str]] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    documentation_url: Optional[str] = None
    key_features: Optional[List[str]] = None
    challenges: Optional[str] = None
    solutions: Optional[str] = None
    is_published: Optional[bool] = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    portfolio_id: str
    created_at: dt.datetime
    updated_at: dt.datetime


# ---------- Architecture ----------
class NodeBase(BaseModel):
    node_type: str
    name: str
    description: Optional[str] = None
    technology: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    position_x: int = 0
    position_y: int = 0
    metadata_json: dict = {}


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    node_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    technology: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    metadata_json: Optional[dict] = None


class NodeOut(NodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str


class EdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None


class EdgeOut(EdgeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str


class EndpointBase(BaseModel):
    method: str
    path: str
    description: Optional[str] = None
    requires_auth: bool = False
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_codes: List[int] = []


class EndpointCreate(EndpointBase):
    pass


class EndpointOut(EndpointBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str


class DiagramOut(BaseModel):
    nodes: List[NodeOut]
    edges: List[EdgeOut]


class SearchResult(BaseModel):
    type: str
    label: str
    portfolio_slug: str
    project_slug: Optional[str] = None


# ---------- Diagram export / import ("architecture as code") ----------
class DiagramNodeItem(NodeBase):
    """A node inside an exported/imported diagram document.

    ``key`` is a document-local identifier so that edges can be referenced
    before the nodes exist in the database.
    """
    key: str = Field(min_length=1, max_length=64)


class DiagramEdgeItem(BaseModel):
    source_key: str
    target_key: str
    label: Optional[str] = None


class DiagramProjectInfo(BaseModel):
    id: str
    slug: str
    name: str
    portfolio_slug: Optional[str] = None


class DiagramDocument(BaseModel):
    format: Literal["archport-diagram"] = "archport-diagram"
    version: int = 1
    project: Optional[DiagramProjectInfo] = None
    nodes: List[DiagramNodeItem] = []
    edges: List[DiagramEdgeItem] = []

    @model_validator(mode="after")
    def _validate_keys(self) -> "DiagramDocument":
        keys = [node.key for node in self.nodes]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate node keys in the diagram document")
        known = set(keys)
        for edge in self.edges:
            for role, key in (("source", edge.source_key), ("target", edge.target_key)):
                if key not in known:
                    raise ValueError(f"Edge {role}_key '{key}' does not match any node")
        return self


class MermaidImportRequest(BaseModel):
    mermaid: str = Field(min_length=1, max_length=200_000)


class ImportResult(BaseModel):
    nodes_created: int
    edges_created: int
    nodes_deleted: int = 0
    edges_deleted: int = 0
