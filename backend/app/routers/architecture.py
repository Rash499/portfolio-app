from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, get_owned_project

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
