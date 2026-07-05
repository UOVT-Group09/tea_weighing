# tests/test_payments.py
from unittest.mock import patch
from src.app import create_app

def login(client):
    with client.session_transaction() as sess:
        sess["operator_id"] = 1
        sess["operator_username"] = "admin"

def test_payments_index_renders():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    login(client)
    
    resp = client.get("/payments/")
    assert resp.status_code == 200
   
    assert b"Payments" in resp.data