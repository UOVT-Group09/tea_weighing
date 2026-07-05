"""Tests for src/weights.py — the Weight Entry blueprint (§5.2 integration).

Owner of the module under test: K.G.C. Ravishan (Lead Dev — Weights & Smart
Checks).

These exercise the Flask routes through the test client. The DB-touching
helpers (``_farmers``, ``_recent_entries``, ``_insert_record``) and
``checks.check`` are monkeypatched so no real MySQL connection is needed.
"""

import pytest

from src import checks, weights
from src.app import create_app
from src.db import DatabaseError

SAMPLE_FARMERS = [
    {"farmer_id": 1, "name": "R. Perera"},
    {"farmer_id": 2, "name": "S. Kumari"},
]


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _login(client):
    with client.session_transaction() as sess:
        sess["operator_id"] = 1
        sess["operator_username"] = "admin"


# ---------------------------------------------------------------------------
# GET /weights/
# ---------------------------------------------------------------------------


def test_index_redirects_to_login_when_not_authenticated(client):
    resp = client.get("/weights/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_index_shows_empty_state_when_no_farmers(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: [])

    resp = client.get("/weights/")

    assert resp.status_code == 200
    assert b"No farmers yet" in resp.data


def test_index_lists_farmers_and_recent_entries(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)
    monkeypatch.setattr(
        weights,
        "_recent_entries",
        lambda farmer_id: [
            {"record_id": 1, "date": "2026-07-01", "weight_kg": 11.8, "flagged": False},
            {"record_id": 2, "date": "2026-06-30", "weight_kg": 90.0, "flagged": True},
        ],
    )

    resp = client.get("/weights/?farmer_id=1")

    assert resp.status_code == 200
    assert b"R. Perera" in resp.data
    assert b"11.8" in resp.data
    assert b"90.0" in resp.data


def test_index_falls_back_to_first_farmer_when_requested_id_unknown(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)
    monkeypatch.setattr(weights, "_recent_entries", lambda farmer_id: [])

    resp = client.get("/weights/?farmer_id=999")

    assert resp.status_code == 200
    # farmers[0] ("R. Perera") should be selected, not the unknown id.
    assert b"selected" in resp.data


def test_index_shows_friendly_message_when_database_unavailable(client, monkeypatch):
    _login(client)

    def boom():
        raise DatabaseError("nope")

    monkeypatch.setattr(weights, "_farmers", boom)

    resp = client.get("/weights/")

    assert resp.status_code == 200
    assert b"No farmers yet" in resp.data or b"Database" in resp.data


# ---------------------------------------------------------------------------
# POST /weights/save
# ---------------------------------------------------------------------------


def test_save_requires_login(client):
    resp = client.post("/weights/save", data={})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_save_missing_farmer_shows_error(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "", "date": "2026-07-01", "weight_kg": "12.5"},
    )

    assert resp.status_code == 200
    assert b"Please choose a farmer" in resp.data


def test_save_non_numeric_weight_shows_error(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "abc"},
    )

    assert resp.status_code == 200
    assert b"Weight must be a number" in resp.data


def test_save_non_positive_weight_shows_error(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "0"},
    )

    assert resp.status_code == 200
    assert b"Weight must be positive" in resp.data


def test_save_future_date_shows_error(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2999-01-01", "weight_kg": "12.5"},
    )

    assert resp.status_code == 200
    assert b"Future dates are not allowed" in resp.data


def test_save_ok_result_inserts_unflagged_and_redirects(client, monkeypatch):
    _login(client)
    inserted = {}

    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)
    monkeypatch.setattr(checks, "check", lambda farmer_id, weight: checks.OK)

    def fake_insert(farmer_id, date_str, weight, *, flagged):
        inserted.update(farmer_id=farmer_id, date_str=date_str, weight=weight, flagged=flagged)

    monkeypatch.setattr(weights, "_insert_record", fake_insert)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "12.5"},
    )

    assert resp.status_code == 302
    assert "farmer_id=1" in resp.headers["Location"]
    assert inserted == {
        "farmer_id": 1,
        "date_str": "2026-07-01",
        "weight": 12.5,
        "flagged": False,
    }


def test_save_warn_result_renders_confirmation_without_inserting(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(weights, "_farmers", lambda: SAMPLE_FARMERS)
    monkeypatch.setattr(checks, "check", lambda farmer_id, weight: checks.WARN_OUT_OF_RANGE)
    monkeypatch.setattr(weights, "_recent_average", lambda farmer_id: 12.0)

    def fail_insert(*args, **kwargs):
        raise AssertionError("a flagged entry must be confirmed before it is saved")

    monkeypatch.setattr(weights, "_insert_record", fail_insert)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "90.0"},
    )

    assert resp.status_code == 200
    assert b"Please confirm" in resp.data
    assert b"R. Perera" in resp.data
    assert b"Confirm" in resp.data


def test_save_database_error_flashes_and_redirects(client, monkeypatch):
    _login(client)

    def boom():
        raise DatabaseError("down")

    monkeypatch.setattr(weights, "_farmers", boom)

    resp = client.post(
        "/weights/save",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "12.5"},
    )

    assert resp.status_code == 302
    assert "/weights/" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# POST /weights/confirm
# ---------------------------------------------------------------------------


def test_confirm_requires_login(client):
    resp = client.post("/weights/confirm", data={})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_confirm_inserts_flagged_record_and_redirects(client, monkeypatch):
    _login(client)
    inserted = {}

    def fake_insert(farmer_id, date_str, weight, *, flagged):
        inserted.update(farmer_id=farmer_id, date_str=date_str, weight=weight, flagged=flagged)

    monkeypatch.setattr(weights, "_insert_record", fake_insert)

    resp = client.post(
        "/weights/confirm",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "90.0"},
    )

    assert resp.status_code == 302
    assert "farmer_id=1" in resp.headers["Location"]
    assert inserted == {
        "farmer_id": 1,
        "date_str": "2026-07-01",
        "weight": 90.0,
        "flagged": True,
    }


def test_confirm_invalid_entry_does_not_insert(client, monkeypatch):
    _login(client)

    def fail_insert(*args, **kwargs):
        raise AssertionError("an invalid entry must never be inserted")

    monkeypatch.setattr(weights, "_insert_record", fail_insert)

    resp = client.post(
        "/weights/confirm",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "not-a-number"},
    )

    assert resp.status_code == 302
    assert "/weights/" in resp.headers["Location"]


def test_confirm_database_error_flashes_and_redirects(client, monkeypatch):
    _login(client)

    def boom(*args, **kwargs):
        raise DatabaseError("down")

    monkeypatch.setattr(weights, "_insert_record", boom)

    resp = client.post(
        "/weights/confirm",
        data={"farmer_id": "1", "date": "2026-07-01", "weight_kg": "90.0"},
    )

    assert resp.status_code == 302
    assert "/weights/" in resp.headers["Location"]
