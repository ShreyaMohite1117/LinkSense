from datetime import datetime, timedelta, timezone


def create(client, headers, **body):
    return client.post("/api/links", json=body, headers=headers)


def test_create_and_redirect(client, auth_headers):
    res = create(client, auth_headers, url="github.com/pallets/flask")
    assert res.status_code == 201
    link = res.get_json()["link"]
    assert link["original_url"] == "https://github.com/pallets/flask"

    res = client.get(f"/{link['short_code']}", headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
    assert res.status_code == 302
    assert res.headers["Location"] == "https://github.com/pallets/flask"

    detail = client.get(f"/api/links/{link['id']}", headers=auth_headers).get_json()["link"]
    assert detail["clicks"] == 1


def test_custom_alias_and_conflict(client, auth_headers):
    assert create(client, auth_headers, url="https://python.org", alias="py-home").status_code == 201
    assert create(client, auth_headers, url="https://python.org", alias="py-home").status_code == 409
    assert create(client, auth_headers, url="https://python.org", alias="api").status_code == 400


def test_invalid_url(client, auth_headers):
    assert create(client, auth_headers, url="javascript:alert(1)").status_code == 400
    assert create(client, auth_headers, url="not a url").status_code == 400


def test_phishing_url_blocked(client, auth_headers):
    res = create(client, auth_headers, url="http://paypal-secure-login.verify-account.tk/webscr/index.php")
    assert res.status_code == 422
    assert res.get_json()["risk"]["verdict"] == "malicious"


def test_password_protected(client, auth_headers):
    link = create(client, auth_headers, url="https://python.org", password="open-sesame").get_json()["link"]
    res = client.get(f"/{link['short_code']}")
    assert "/p/" in res.headers["Location"]
    assert client.post(f"/api/r/{link['short_code']}/unlock", json={"password": "bad"}).status_code == 401
    ok = client.post(f"/api/r/{link['short_code']}/unlock", json={"password": "open-sesame"})
    assert ok.get_json()["url"] == "https://python.org"


def test_max_clicks(client, auth_headers):
    link = create(client, auth_headers, url="https://python.org", max_clicks=1).get_json()["link"]
    assert client.get(f"/{link['short_code']}").headers["Location"] == "https://python.org"
    assert "expired" in client.get(f"/{link['short_code']}").headers["Location"]


def test_expiry_in_past_rejected(client, auth_headers):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert create(client, auth_headers, url="https://python.org", expires_at=past).status_code == 400


def test_update_invalidates_cache(client, auth_headers):
    link = create(client, auth_headers, url="https://python.org").get_json()["link"]
    client.get(f"/{link['short_code']}")  # warm cache
    client.patch(f"/api/links/{link['id']}", json={"url": "https://pypi.org"}, headers=auth_headers)
    assert client.get(f"/{link['short_code']}").headers["Location"] == "https://pypi.org"


def test_cannot_touch_someone_elses_link(client, auth_headers):
    link = create(client, auth_headers, url="https://python.org").get_json()["link"]
    other = client.post("/api/auth/signup", json={"name": "Eve", "email": "eve@example.com", "password": "hello1234"})
    headers = {"Authorization": f"Bearer {other.get_json()['access_token']}"}
    assert client.delete(f"/api/links/{link['id']}", headers=headers).status_code == 404


def test_qr_code(client, auth_headers):
    link = create(client, auth_headers, url="https://python.org").get_json()["link"]
    res = client.get(f"/api/qr/{link['short_code']}")
    assert res.status_code == 200 and res.mimetype == "image/png"


def test_unknown_code_redirects_to_404_page(client):
    assert "not-found" in client.get("/doesnotexist").headers["Location"]
