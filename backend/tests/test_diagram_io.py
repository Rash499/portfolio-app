"""Tests for the diagram export/import ("architecture as code") feature."""

import pytest

from app import diagram_io, models


def _create_portfolio(client, headers, slug="rashmika", is_public=True):
    return client.post("/api/portfolios", json={
        "slug": slug, "title": "Rashmika Dilmin", "skills": ["Kubernetes"],
        "is_public": is_public,
    }, headers=headers)


def _create_project(client, headers, portfolio_id, is_published=True):
    return client.post(f"/api/projects/portfolio/{portfolio_id}", json={
        "slug": "event-intel", "name": "Global Event Intelligence Platform",
        "technologies": ["FastAPI", "SQLite"], "is_published": is_published,
    }, headers=headers).json()


def _seed_diagram(client, headers, project_id):
    """Two nodes (backend + database) and one labelled edge."""
    api_node = client.post(f"/api/projects/{project_id}/nodes", json={
        "node_type": "backend", "name": "Ingestion API", "technology": "FastAPI",
        "version": "0.4.1", "environment": "production",
        "position_x": 120, "position_y": 40,
        "metadata_json": {"endpoints": ["GET /events"], "owner": "platform-team"},
    }, headers=headers).json()
    db_node = client.post(f"/api/projects/{project_id}/nodes", json={
        "node_type": "database", "name": "SQLite Store", "technology": "SQLite",
        "position_x": 420, "position_y": 40,
    }, headers=headers).json()
    client.post(f"/api/projects/{project_id}/edges", json={
        "source_node_id": api_node["id"], "target_node_id": db_node["id"], "label": "writes",
    }, headers=headers)
    return api_node, db_node


def _setup(client, auth_headers, **portfolio_kwargs):
    portfolio = _create_portfolio(client, auth_headers, **portfolio_kwargs).json()
    project = _create_project(client, auth_headers, portfolio["id"])
    nodes = _seed_diagram(client, auth_headers, project["id"])
    return portfolio, project, nodes


# --------------------------------------------------------------------------- #
# JSON export
# --------------------------------------------------------------------------- #
def test_export_json_is_lossless(client, auth_headers):
    portfolio, project, _ = _setup(client, auth_headers)

    r = client.get(f"/api/projects/{project['id']}/export/json", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()

    assert body["format"] == "archport-diagram"
    assert body["version"] == 1
    assert body["project"]["slug"] == "event-intel"
    assert body["project"]["portfolio_slug"] == portfolio["slug"]

    keys = {node["name"]: node["key"] for node in body["nodes"]}
    assert set(keys) == {"Ingestion API", "SQLite Store"}

    api_node = next(n for n in body["nodes"] if n["name"] == "Ingestion API")
    assert api_node["metadata_json"] == {"endpoints": ["GET /events"], "owner": "platform-team"}
    assert api_node["position_x"] == 120 and api_node["position_y"] == 40
    assert api_node["version"] == "0.4.1" and api_node["environment"] == "production"

    assert body["edges"] == [{
        "source_key": keys["Ingestion API"],
        "target_key": keys["SQLite Store"],
        "label": "writes",
    }]


def test_export_json_offers_a_download_filename(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    r = client.get(f"/api/projects/{project['id']}/export/json", headers=auth_headers)
    assert "rashmika-event-intel-architecture.json" in r.headers["content-disposition"]


def test_private_project_export_is_hidden(client, auth_headers):
    portfolio = _create_portfolio(client, auth_headers, is_public=False).json()
    project = _create_project(client, auth_headers, portfolio["id"], is_published=False)

    anonymous = client.get(f"/api/projects/{project['id']}/export/mermaid")
    assert anonymous.status_code == 404

    client.post("/api/auth/register", json={
        "email": "other@example.com", "username": "other", "password": "password123",
    })
    login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "password123"})
    intruder = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get(f"/api/projects/{project['id']}/export/json", headers=intruder).status_code == 404


def test_published_project_export_is_public(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    r = client.get(f"/api/projects/{project['id']}/export/mermaid")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")


# --------------------------------------------------------------------------- #
# Mermaid export
# --------------------------------------------------------------------------- #
def test_export_mermaid_uses_shapes_and_styles(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    mermaid = client.get(f"/api/projects/{project['id']}/export/mermaid", headers=auth_headers).text

    assert mermaid.startswith("%% Architecture diagram exported")
    assert "%% Global Event Intelligence Platform" in mermaid
    assert "flowchart TD" in mermaid
    assert '[("SQLite Store<br/>SQLite<br/>[database]")]' in mermaid
    assert '"Ingestion API<br/>FastAPI<br/>[backend]"' in mermaid
    assert "-->|writes|" in mermaid
    assert "classDef storage" in mermaid and "classDef service" in mermaid


# --------------------------------------------------------------------------- #
# JSON import
# --------------------------------------------------------------------------- #
def test_json_round_trip_replaces_the_diagram(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    document = client.get(f"/api/projects/{project['id']}/export/json", headers=auth_headers).json()

    r = client.post(
        f"/api/projects/{project['id']}/import",
        json=document, params={"mode": "replace"}, headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == {
        "nodes_created": 2, "edges_created": 1, "nodes_deleted": 2, "edges_deleted": 1,
    }

    diagram = client.get(f"/api/projects/{project['id']}/diagram").json()
    assert {n["name"] for n in diagram["nodes"]} == {"Ingestion API", "SQLite Store"}
    api_node = next(n for n in diagram["nodes"] if n["name"] == "Ingestion API")
    assert api_node["metadata_json"] == {"endpoints": ["GET /events"], "owner": "platform-team"}
    assert api_node["position_x"] == 120 and api_node["version"] == "0.4.1"
    assert len(diagram["edges"]) == 1 and diagram["edges"][0]["label"] == "writes"


def test_merge_import_appends_a_fragment(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    payload = {
        "nodes": [
            {"key": "argo", "node_type": "argo_cd", "name": "Argo CD", "technology": "Argo CD"},
            {"key": "prom", "node_type": "monitoring", "name": "Prometheus", "technology": "Prometheus"},
        ],
        "edges": [{"source_key": "prom", "target_key": "argo", "label": "alerts"}],
    }
    r = client.post(f"/api/projects/{project['id']}/import", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {
        "nodes_created": 2, "edges_created": 1, "nodes_deleted": 0, "edges_deleted": 0,
    }

    diagram = client.get(f"/api/projects/{project['id']}/diagram").json()
    assert len(diagram["nodes"]) == 4
    assert len(diagram["edges"]) == 2


def test_import_rejects_unknown_edge_keys(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    payload = {
        "nodes": [{"key": "a", "node_type": "backend", "name": "API"}],
        "edges": [{"source_key": "a", "target_key": "ghost"}],
    }
    r = client.post(f"/api/projects/{project['id']}/import", json=payload, headers=auth_headers)
    assert r.status_code == 422


def test_import_requires_authentication(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    r = client.post(f"/api/projects/{project['id']}/import", json={"nodes": []})
    assert r.status_code == 401


def test_cannot_import_into_someone_elses_project(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    client.post("/api/auth/register", json={
        "email": "other@example.com", "username": "other", "password": "password123",
    })
    login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "password123"})
    other = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.post(
        f"/api/projects/{project['id']}/import",
        json={"nodes": [{"key": "a", "node_type": "backend", "name": "API"}]},
        headers=other,
    )
    assert r.status_code == 403


# --------------------------------------------------------------------------- #
# Mermaid import
# --------------------------------------------------------------------------- #
def test_mermaid_import_creates_a_diagram(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    mermaid = """%% hand written diagram
flowchart TD
    subgraph Delivery
      ci["Build<br/>[ci_pipeline]"]
    end
    ci -->|deploys| api["Reporting API<br/>[backend]"]
    db[("Metrics DB<br/>[database]")]
    api --> db
classDef ci_pipeline fill:#fff
"""
    r = client.post(
        f"/api/projects/{project['id']}/import/mermaid",
        json={"mermaid": mermaid}, params={"mode": "replace"}, headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == {
        "nodes_created": 3, "edges_created": 2, "nodes_deleted": 2, "edges_deleted": 1,
    }

    diagram = client.get(f"/api/projects/{project['id']}/diagram").json()
    by_name = {n["name"]: n for n in diagram["nodes"]}
    assert by_name["Build"]["node_type"] == "ci_pipeline"
    assert by_name["Metrics DB"]["node_type"] == "database"
    assert by_name["Reporting API"]["node_type"] == "backend"
    assert sorted(e["label"] or "" for e in diagram["edges"]) == ["", "deploys"]


def test_mermaid_import_rejects_unreadable_syntax(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    r = client.post(
        f"/api/projects/{project['id']}/import/mermaid",
        json={"mermaid": "flowchart TD\n    A --> @@@\n"}, headers=auth_headers,
    )
    assert r.status_code == 422
    assert "could not read" in r.json()["detail"]


def test_mermaid_import_rejects_empty_body(client, auth_headers):
    _, project, _ = _setup(client, auth_headers)
    r = client.post(
        f"/api/projects/{project['id']}/import/mermaid",
        json={"mermaid": ""}, headers=auth_headers,
    )
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Codec unit tests
# --------------------------------------------------------------------------- #
def test_to_mermaid_skips_dangling_edges_and_escapes_labels():
    node = models.ArchitectureNode(
        id="abc", project_id="p", node_type="backend",
        name='Say "hi" | now', technology="FastAPI",
    )
    stray = models.ArchitectureEdge(
        id="e1", project_id="p", source_node_id="abc", target_node_id="gone",
    )

    mermaid = diagram_io.to_mermaid([node], [stray])
    assert "gone" not in mermaid
    assert '"Say \'hi\' | now<br/>FastAPI<br/>[backend]"' in mermaid
    assert mermaid.count("n_abc") == 2  # node definition + class assignment


def test_to_mermaid_neutralises_the_end_keyword():
    node = models.ArchitectureNode(id="u1", project_id="p", node_type="user", name="end")
    mermaid = diagram_io.to_mermaid([node], [])
    assert 'n_u1(("End<br/>[user]"))' in mermaid


def test_from_mermaid_reads_front_matter_and_arrow_styles():
    document = diagram_io.from_mermaid(
        "---\ntitle: Demo\nconfig:\n  theme: default\n---\n"
        "flowchart LR\n"
        '    a["Ingestion API<br/>FastAPI<br/>[backend]"]\n'
        '    b[("SQLite<br/>[database]")]\n'
        "    a --writes--> b\n"
        "    classDef backend fill:#fff\n"
    )
    assert [n.key for n in document.nodes] == ["a", "b"]
    assert document.nodes[0].technology == "FastAPI"
    assert document.nodes[1].node_type == "database"
    assert document.edges[0].label == "writes"
    assert (document.nodes[0].position_x, document.nodes[1].position_x) == (80, 300)


def test_from_mermaid_rejects_unreadable_input():
    with pytest.raises(diagram_io.MermaidParseError):
        diagram_io.from_mermaid("flowchart TD\n    A --> @@@\n")
    with pytest.raises(diagram_io.MermaidParseError):
        diagram_io.from_mermaid("   \n")
