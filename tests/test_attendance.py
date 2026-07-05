from datetime import date
from .conftest import login


# ---------------------------
# Attendance page loads
# ---------------------------
def test_attendance_index_loads(client):
    login(client)

    resp = client.get("/attendance/")
    assert resp.status_code == 200


# ---------------------------
# Mark attendance success
# ---------------------------
def test_mark_attendance_success(client):
    login(client)

    resp = client.post(
        "/attendance/mark",
        data={
            "plucker_id": 1,
            "present": "true",
            "date": date.today().isoformat()
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Attendance updated successfully" in resp.data


# ---------------------------
# Invalid date format
# ---------------------------
def test_mark_attendance_invalid_date(client):
    login(client)

    resp = client.post(
        "/attendance/mark",
        data={
            "plucker_id": 1,
            "present": "true",
            "date": "invalid-date"
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Invalid date format" in resp.data


# ---------------------------
# Future date validation
# ---------------------------
def test_mark_attendance_future_date(client):
    login(client)

    resp = client.post(
        "/attendance/mark",
        data={
            "plucker_id": 1,
            "present": "true",
            "date": "2099-01-01"
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Future dates are not allowed" in resp.data


# ---------------------------
# Add plucker page loads
# ---------------------------
def test_add_plucker_page_loads(client):
    login(client)

    resp = client.get("/attendance/pluckers/add")
    assert resp.status_code == 200


# ---------------------------
# Add plucker success
# ---------------------------
def test_add_plucker_success(client):
    login(client)

    resp = client.post(
        "/attendance/pluckers/add",
        data={
            "name": "Test Plucker",
            "daily_rate": "1500"
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Plucker added successfully" in resp.data


# ---------------------------
# Invalid daily rate
# ---------------------------
def test_add_plucker_invalid_rate(client):
    login(client)

    resp = client.post(
        "/attendance/pluckers/add",
        data={
            "name": "Bad Plucker",
            "daily_rate": "-100"
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Invalid daily rate" in resp.data


# ---------------------------
# Empty name validation
# ---------------------------
def test_add_plucker_empty_name(client):
    login(client)

    resp = client.post(
        "/attendance/pluckers/add",
        data={
            "name": "",
            "daily_rate": "1000"
        },
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Name is required" in resp.data