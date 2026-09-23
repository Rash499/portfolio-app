from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import diagram_io, models, schemas
from app.deps import get_current_user, get_optional_user, get_owned_project

router = APIRouter(prefix="/api", tags=["architecture"])


def _project_or_404(project_id: str, db: Session) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------- Nodes ----------
@router.post("/projects/{project_id}/nodes", response_model=schemas.NodeOut, status_code=201)
def create_node(project_id: str, payload: schemas.NodeCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    get_owned_project(project_id, db, user)
    node = models.ArchitectureNode(project_id=project_id, **payload.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.put("/nodes/{node_id}", response_model=schemas.NodeOut)
def update_node(node_id: str, payload: schemas.NodeUpdate, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    node = db.query(models.ArchitectureNode).filter(models.ArchitectureNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    get_owned_project(node.project_id, db, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(node, k, v)
    db.commit()
    db.refresh(node)
    return node


@router.delete("/nodes/{node_id}", status_code=204)
def delete_node(node_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    node = db.query(models.ArchitectureNode).filter(models.ArchitectureNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    get_owned_project(node.project_id, db, user)
    db.delete(node)
    db.commit()
    return None


# ---------- Edges ----------
@router.post("/projects/{project_id}/edges", response_model=schemas.EdgeOut, status_code=201)
def create_edge(project_id: str, payload: schemas.EdgeCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    get_owned_project(project_id, db, user)
    edge = models.ArchitectureEdge(project_id=project_id, **payload.model_dump())
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


@router.delete("/edges/{edge_id}", status_code=204)
def delete_edge(edge_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    edge = db.query(models.ArchitectureEdge).filter(models.ArchitectureEdge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    get_owned_project(edge.project_id, db, user)
    db.delete(edge)
    db.commit()
    return None


# ---------- Diagram (nodes+edges together) ----------
@router.get("/projects/{project_id}/diagram", response_model=schemas.DiagramOut)
def get_diagram(project_id: str, db: Session = Depends(get_db)):
    project = _project_or_404(project_id, db)
    return schemas.DiagramOut(nodes=project.nodes, edges=project.edges)


# ---------- API Endpoints (API Explorer) ----------
@router.post("/projects/{project_id}/endpoints", response_model=schemas.EndpointOut, status_code=201)
def create_endpoint(project_id: str, payload: schemas.EndpointCreate, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    get_owned_project(project_id, db, user)
    endpoint = models.ApiEndpoint(project_id=project_id, **payload.model_dump())
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


@router.get("/projects/{project_id}/endpoints", response_model=List[schemas.EndpointOut])
def list_endpoints(project_id: str, db: Session = Depends(get_db)):
    project = _project_or_404(project_id, db)
    return project.endpoints


@router.delete("/endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(endpoint_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    endpoint = db.query(models.ApiEndpoint).filter(models.ApiEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    get_owned_project(endpoint.project_id, db, user)
    db.delete(endpoint)
    db.commit()
    return None


# ---------- Export / import ("architecture as code") ----------
def _readable_project(project_id: str, db: Session, user: Optional[models.User]) -> models.Project:
    """A project is readable by its owner and by anyone once it is published
    inside a public portfolio (so public pages can offer the Mermaid export)."""
    project = _project_or_404(project_id, db)
    if user is not None and project.portfolio.owner_id == user.id:
        return project
    if project.is_published and project.portfolio.is_public:
        return project
    raise HTTPException(status_code=404, detail="Project not found")


@router.get("/projects/{project_id}/export/json")
def export_diagram_json(
    project_id: str,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_optional_user),
):
    """Lossless JSON bundle: every node field, edge and canvas position."""
    project = _readable_project(project_id, db, user)
    document = diagram_io.to_document(project)
    filename = diagram_io.export_filename(project, "json")
    return JSONResponse(
        content=document.model_dump(),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/export/mermaid", response_class=PlainTextResponse)
def export_diagram_mermaid(
    project_id: str,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_optional_user),
):
    """Mermaid flowchart source, ready to paste into a README or mermaid.live."""
    project = _readable_project(project_id, db, user)
    return PlainTextResponse(
        diagram_io.to_mermaid(project.nodes, project.edges, title=project.name),
        media_type="text/plain; charset=utf-8",
    )


@router.post("/projects/{project_id}/import", response_model=schemas.ImportResult)
def import_diagram(
    project_id: str,
    document: schemas.DiagramDocument,
    mode: Literal["merge", "replace"] = Query("merge"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Import a JSON diagram bundle previously produced by the exporter."""
    project = get_owned_project(project_id, db, user)
    return diagram_io.apply_document(project, document, db, mode=mode)


@router.post("/projects/{project_id}/import/mermaid", response_model=schemas.ImportResult)
def import_diagram_mermaid(
    project_id: str,
    payload: schemas.MermaidImportRequest,
    mode: Literal["merge", "replace"] = Query("merge"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Import a Mermaid flowchart (the exporter's subset, plus simple hand-written charts)."""
    project = get_owned_project(project_id, db, user)
    try:
        document = diagram_io.from_mermaid(payload.mermaid)
    except diagram_io.MermaidParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return diagram_io.apply_document(project, document, db, mode=mode)
