def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "email": "a@example.com", "username": "alice", "password": "password123",
    })
    assert r.status_code == 201
    assert "access_token" in r.json()

    r = client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "b@example.com", "username": "bob", "password": "password123",
    })
    r = client.post("/api/auth/login", json={"email": "b@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_duplicate_email_rejected(client):
    payload = {"email": "c@example.com", "username": "carol", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    r = client.post("/api/auth/register", json={**payload, "username": "carol2"})
    assert r.status_code == 409


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_token(client, auth_headers):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "dev@example.com"


def test_refresh_token_flow(client):
    client.post("/api/auth/register", json={
        "email": "d@example.com", "username": "dana", "password": "password123",
    })
    login = client.post("/api/auth/login", json={"email": "d@example.com", "password": "password123"})
    refresh_token = login.json()["refresh_token"]
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_rejects_access_token(client, auth_headers):
    access_token = auth_headers["Authorization"].split(" ")[1]
    r = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401
