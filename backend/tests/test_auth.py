def test_signup_and_login(client):
    res = client.post("/api/auth/signup", json={"name": "Ravi", "email": "ravi@example.com", "password": "hello1234"})
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "ravi@example.com"

    res = client.post("/api/auth/login", json={"email": "RAVI@example.com", "password": "hello1234"})
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_duplicate_email_rejected(client):
    body = {"name": "Ravi", "email": "dup@example.com", "password": "hello1234"}
    client.post("/api/auth/signup", json=body)
    assert client.post("/api/auth/signup", json=body).status_code == 409


def test_weak_password_rejected(client):
    res = client.post("/api/auth/signup", json={"name": "Ravi", "email": "r@example.com", "password": "short"})
    assert res.status_code == 400


def test_wrong_password(client, auth_headers):
    res = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "nope12345"})
    assert res.status_code == 401


def test_protected_route_needs_token(client):
    assert client.get("/api/links").status_code == 401


def test_refresh_token(client):
    res = client.post("/api/auth/signup", json={"name": "Kiran", "email": "k@example.com", "password": "hello1234"})
    refresh = res.get_json()["refresh_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200 and res.get_json()["access_token"]


def test_api_key_auth(client, auth_headers):
    key = client.post("/api/auth/api-key", headers=auth_headers).get_json()["api_key"]
    res = client.post("/api/links", json={"url": "https://python.org"}, headers={"X-API-Key": key})
    assert res.status_code == 201
