def _create_portfolio(client, headers, slug="rashmika", is_public=True):
    return client.post("/api/portfolios", json={
        "slug": slug, "title": "Rashmika Dilmin", "professional_title": "Cloud Security Engineer",
        "about": "DevOps engineer.", "skills": ["Azure", "Kubernetes"], "is_public": is_public,
    }, headers=headers)


def test_create_and_list_portfolio(client, auth_headers):
    r = _create_portfolio(client, auth_headers)
    assert r.status_code == 201
    assert r.json()["slug"] == "rashmika"

    r = client.get("/api/portfolios/me", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_portfolio_requires_auth_to_create(client):
    r = client.post("/api/portfolios", json={"slug": "x", "title": "X"})
    assert r.status_code == 401


def test_duplicate_slug_rejected(client, auth_headers):
    _create_portfolio(client, auth_headers)
    r = _create_portfolio(client, auth_headers)
    assert r.status_code == 409


def test_project_and_architecture_flow(client, auth_headers):
    portfolio = _create_portfolio(client, auth_headers).json()

    project = client.post(f"/api/projects/portfolio/{portfolio['id']}", json={
        "slug": "event-intel", "name": "Global Event Intelligence Platform",
        "short_description": "GDELT ingestion + local LLM classification.",
        "technologies": ["FastAPI", "React", "Ollama"], "is_published": True,
    }, headers=auth_headers).json()
    assert project["slug"] == "event-intel"

    node1 = client.post(f"/api/projects/{project['id']}/nodes", json={
        "node_type": "backend", "name": "Ingestion API", "technology": "FastAPI",
        "metadata_json": {"endpoints": ["GET /events"]},
    }, headers=auth_headers).json()
    node2 = client.post(f"/api/projects/{project['id']}/nodes", json={
        "node_type": "database", "name": "SQLite Store", "technology": "SQLite",
    }, headers=auth_headers).json()

    edge = client.post(f"/api/projects/{project['id']}/edges", json={
        "source_node_id": node1["id"], "target_node_id": node2["id"], "label": "writes",
    }, headers=auth_headers)
    assert edge.status_code == 201

    diagram = client.get(f"/api/projects/{project['id']}/diagram")
    assert diagram.status_code == 200
    body = diagram.json()
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1

    endpoint = client.post(f"/api/projects/{project['id']}/endpoints", json={
        "method": "GET", "path": "/api/events", "description": "List classified events",
        "status_codes": [200, 401],
    }, headers=auth_headers)
    assert endpoint.status_code == 201


def test_public_portfolio_hides_unpublished_projects(client, auth_headers):
    portfolio = _create_portfolio(client, auth_headers).json()
    client.post(f"/api/projects/portfolio/{portfolio['id']}", json={
        "slug": "draft", "name": "Draft project", "is_published": False,
    }, headers=auth_headers)

    r = client.get(f"/api/portfolios/public/{portfolio['slug']}/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_cannot_edit_other_users_portfolio(client, auth_headers):
    portfolio = _create_portfolio(client, auth_headers).json()

    client.post("/api/auth/register", json={
        "email": "other@example.com", "username": "other", "password": "password123",
    })
    other_login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    r = client.put(f"/api/portfolios/{portfolio['id']}", json={"title": "Hacked"}, headers=other_headers)
    assert r.status_code == 403


def test_search_finds_public_project(client, auth_headers):
    portfolio = _create_portfolio(client, auth_headers).json()
    client.post(f"/api/projects/portfolio/{portfolio['id']}", json={
        "slug": "k8s-platform", "name": "Kubernetes Platform", "technologies": ["Kubernetes", "Argo CD"],
        "is_published": True,
    }, headers=auth_headers)

    r = client.get("/api/search", params={"q": "kubernetes"})
    assert r.status_code == 200
    assert any(res["type"] == "project" for res in r.json())
