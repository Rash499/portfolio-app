"""
Idempotent demo-data seeder for the Interactive System Architecture Portfolio.

Run from backend/:
    python -m seed.seed_mock_data

The script creates one demo user, one public portfolio, and three public projects
with interactive architecture nodes, edges, and API endpoint documentation.

Demo login:
    Email: demo@architecture.dev
    Password: Demo123!
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import Base, SessionLocal, engine
from app.security import hash_password


SEED_FILE = Path(__file__).with_name("mock_data.json")


def get_or_create_user(db: Session, data: dict) -> models.User:
    user = db.query(models.User).filter(models.User.email == data["email"]).first()
    if user:
        user.hashed_password = hash_password(data["password"])
        user.username = data["username"]
        user.full_name = data.get("full_name")
        return user

    user = models.User(
        email=data["email"],
        username=data["username"],
        full_name=data.get("full_name"),
        hashed_password=hash_password(data["password"]),
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_portfolio(db: Session, user: models.User, data: dict) -> models.Portfolio:
    portfolio = (
        db.query(models.Portfolio)
        .filter(models.Portfolio.slug == data["slug"])
        .first()
    )
    if portfolio:
        portfolio.owner_id = user.id
        for key, value in data.items():
            setattr(portfolio, key, value)
        return portfolio

    portfolio = models.Portfolio(owner_id=user.id, **data)
    db.add(portfolio)
    db.flush()
    return portfolio


def get_or_create_project(
    db: Session, portfolio: models.Portfolio, data: dict
) -> models.Project:
    project = (
        db.query(models.Project)
        .filter(
            models.Project.portfolio_id == portfolio.id,
            models.Project.slug == data["slug"],
        )
        .first()
    )

    project_fields = {
        key: value
        for key, value in data.items()
        if key not in {"nodes", "edges", "endpoints"}
    }

    if project:
        for key, value in project_fields.items():
            setattr(project, key, value)
    else:
        project = models.Project(portfolio_id=portfolio.id, **project_fields)
        db.add(project)
        db.flush()

    # Re-seed the demo project's architecture so repeated runs stay deterministic.
    db.query(models.ArchitectureEdge).filter(
        models.ArchitectureEdge.project_id == project.id
    ).delete(synchronize_session=False)

    db.query(models.ArchitectureNode).filter(
        models.ArchitectureNode.project_id == project.id
    ).delete(synchronize_session=False)

    db.query(models.ApiEndpoint).filter(
        models.ApiEndpoint.project_id == project.id
    ).delete(synchronize_session=False)

    db.flush()

    node_ids: dict[str, str] = {}

    for item in data.get("nodes", []):
        node = models.ArchitectureNode(
            project_id=project.id,
            node_type=item["node_type"],
            name=item["name"],
            description=item.get("description"),
            technology=item.get("technology"),
            version=item.get("version"),
            environment=item.get("environment"),
            position_x=item.get("x", 0),
            position_y=item.get("y", 0),
            metadata_json=item.get("metadata", {}),
        )
        db.add(node)
        db.flush()
        node_ids[item["key"]] = node.id

    for source_key, target_key, label in data.get("edges", []):
        if source_key not in node_ids or target_key not in node_ids:
            raise ValueError(
                f"Invalid edge in {project.slug}: {source_key} -> {target_key}"
            )

        db.add(
            models.ArchitectureEdge(
                project_id=project.id,
                source_node_id=node_ids[source_key],
                target_node_id=node_ids[target_key],
                label=label,
            )
        )

    for endpoint in data.get("endpoints", []):
        db.add(
            models.ApiEndpoint(
                project_id=project.id,
                method=endpoint["method"],
                path=endpoint["path"],
                description=endpoint.get("description"),
                requires_auth=endpoint.get("requires_auth", False),
                request_body=endpoint.get("request_body"),
                response_body=endpoint.get("response_body"),
                status_codes=endpoint.get("status_codes", []),
            )
        )

    db.flush()
    return project


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))

    db = SessionLocal()
    try:
        user = get_or_create_user(db, data["user"])
        portfolio = get_or_create_portfolio(db, user, data["portfolio"])

        for project_data in data["projects"]:
            get_or_create_project(db, portfolio, project_data)

        db.commit()

        print()
        print("Mock data seeded successfully.")
        print("--------------------------------------------------")
        print("Demo login")
        print("Email:    demo@architecture.dev")
        print("Password: Demo123!")
        print()
        print("Public portfolio:")
        print("http://localhost:5173/p/demo-architect")
        print()
        print("Projects:")
        for project in data["projects"]:
            print(f"  http://localhost:5173/p/demo-architect/{project['slug']}")
        print("--------------------------------------------------")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
