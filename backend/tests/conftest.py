import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import cache, mongo


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    yield app
    for name in mongo.db.list_collection_names():
        mongo.db[name].delete_many({})
    cache.memory.flush()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    res = client.post("/api/auth/signup", json={"name": "Asha", "email": "asha@example.com", "password": "secret123"})
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
