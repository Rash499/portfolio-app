from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, get_owned_portfolio

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("/me", response_model=List[schemas.PortfolioOut])
def list_my_portfolios(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Portfolio).filter(models.Portfolio.owner_id == user.id).all()


@router.post("", response_model=schemas.PortfolioOut, status_code=201)
def create_portfolio(
    payload: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if db.query(models.Portfolio).filter(models.Portfolio.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="Slug already taken")
    portfolio = models.Portfolio(owner_id=user.id, **payload.model_dump())
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=schemas.PortfolioOut)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_portfolio(portfolio_id, db, user)


@router.put("/{portfolio_id}", response_model=schemas.PortfolioOut)
def update_portfolio(
    portfolio_id: str,
    payload: schemas.PortfolioUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    portfolio = get_owned_portfolio(portfolio_id, db, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(portfolio, k, v)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    portfolio = get_owned_portfolio(portfolio_id, db, user)
    db.delete(portfolio)
    db.commit()
    return None


# ---------- Public ----------
@router.get("/public/{slug}", response_model=schemas.PortfolioOut)
def get_public_portfolio(slug: str, db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.slug == slug, models.Portfolio.is_public.is_(True)
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("/public/{slug}/projects", response_model=List[schemas.ProjectOut])
def get_public_portfolio_projects(slug: str, db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.slug == slug, models.Portfolio.is_public.is_(True)
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return [p for p in portfolio.projects if p.is_published]
