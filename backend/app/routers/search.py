from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=List[schemas.SearchResult])
def search(q: str = Query(min_length=1), db: Session = Depends(get_db)):
    results: List[schemas.SearchResult] = []

    portfolios = db.query(models.Portfolio).filter(models.Portfolio.is_public.is_(True)).all()
    for p in portfolios:
        if q.lower() in (p.title or "").lower() or q.lower() in (p.professional_title or "").lower():
            results.append(schemas.SearchResult(type="portfolio", label=p.title, portfolio_slug=p.slug))
        for skill in (p.skills or []):
            if q.lower() in skill.lower():
                results.append(schemas.SearchResult(type="skill", label=f"{skill} — {p.title}", portfolio_slug=p.slug))
                break

    projects = (
        db.query(models.Project)
        .join(models.Portfolio)
        .filter(models.Project.is_published.is_(True), models.Portfolio.is_public.is_(True))
        .all()
    )
    for proj in projects:
        haystack = " ".join([
            proj.name or "", proj.short_description or "", " ".join(proj.technologies or [])
        ]).lower()
        if q.lower() in haystack:
            results.append(schemas.SearchResult(
                type="project", label=proj.name,
                portfolio_slug=proj.portfolio.slug, project_slug=proj.slug,
            ))
        for node in proj.nodes:
            node_haystack = " ".join([node.name or "", node.technology or "", node.node_type or ""]).lower()
            if q.lower() in node_haystack:
                results.append(schemas.SearchResult(
                    type="architecture_node", label=f"{node.name} ({proj.name})",
                    portfolio_slug=proj.portfolio.slug, project_slug=proj.slug,
                ))

    return results[:50]
