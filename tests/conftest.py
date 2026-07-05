import pytest
from src.app import create_app


@pytest.fixture
def app():
    app = create_app()

    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False
    })

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


# ✅ fake login helper (IMPORTANT)
def login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"