"""Integration smoke tests for the app factory.

Owner: H.G.P.C. Sagara (PM & Integration Dev). The full QA/pytest suite
(CRUD, checks, payments) is owned by D.M.N.K. Disanayaka — these tests only
prove the integration layer boots and wires every blueprint together,
without needing a live database.

Run from the tea_weighing/ directory:
    python -m pytest
"""

from src.app import create_app


def make_client():
    app = create_app()
    app.config.update(TESTING=True)
    return app, app.test_client()


def test_app_factory_builds():
    app, _ = make_client()
    assert app is not None


def test_all_blueprints_registered():
    app, _ = make_client()
    for name in ("auth", "farmers", "weights", "payments", "attendance", "reports"):
        assert name in app.blueprints, f"blueprint '{name}' was not registered"


def test_protected_route_redirects_to_login():
    _, client = make_client()
    resp = client.get("/dashboard")
    # Not logged in -> redirect to the login page.
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_page_renders():
    _, client = make_client()
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Operator Login" in resp.data


def test_healthz_endpoint():
    _, client = make_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"
