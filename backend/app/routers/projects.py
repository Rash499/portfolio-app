from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, get_owned_portfolio, get_owned_project

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/portfolio/{portfolio_id}", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    portfolio_id: str,
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    portfolio = get_owned_portfolio(portfolio_id, db, user)
    existing = db.query(models.Project).filter(
        models.Project.portfolio_id == portfolio.id, models.Project.slug == payload.slug
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Project slug already used in this portfolio")
    project = models.Project(portfolio_id=portfolio.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/portfolio/{portfolio_id}", response_model=List[schemas.ProjectOut])
def list_projects(portfolio_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    portfolio = get_owned_portfolio(portfolio_id, db, user)
    return portfolio.projects


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_project(project_id, db, user)


@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: str,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    project = get_owned_project(project_id, db, user)
    db.delete(project)
    db.commit()
    return None


# ---------- Public ----------
@router.get("/public/{portfolio_slug}/{project_slug}", response_model=schemas.ProjectOut)
def get_public_project(portfolio_slug: str, project_slug: str, db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.slug == portfolio_slug, models.Portfolio.is_public.is_(True)
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    project = db.query(models.Project).filter(
        models.Project.portfolio_id == portfolio.id,
        models.Project.slug == project_slug,
        models.Project.is_published.is_(True),
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
