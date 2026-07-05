"""Tests for trend estimate (checks.py) and reports routes.

Owner: P.A.K.N. Dharmarathna — Reports & Trend module tests.
"""

from datetime import date
from unittest.mock import patch

import pytest

from src.app import create_app
from src import checks


def make_client():
    app = create_app()
    app.config.update(TESTING=True)
    return app, app.test_client()


def login(client):
    with client.session_transaction() as sess:
        sess["operator_id"] = 1
        sess["operator_username"] = "admin"


# --- checks.estimate ---------------------------------------------------------


class TestEstimate:
    def test_returns_none_with_fewer_than_three_records(self):
        with patch("src.checks.get_recent_weights", return_value=[10.0, 12.0]):
            assert checks.estimate(1) is None

    def test_returns_none_with_no_records(self):
        with patch("src.checks.get_recent_weights", return_value=[]):
            assert checks.estimate(1) is None

    def test_up_trend_when_latest_above_average(self):
        with patch("src.checks.get_recent_weights", return_value=[15.0, 10.0, 10.0, 10.0]):
            result = checks.estimate(1)
            assert result == (11.25, "up")

    def test_down_trend_when_latest_below_average(self):
        with patch("src.checks.get_recent_weights", return_value=[8.0, 12.0, 12.0, 12.0]):
            result = checks.estimate(1)
            assert result == (11.0, "down")

    def test_down_trend_when_latest_equals_average(self):
        with patch("src.checks.get_recent_weights", return_value=[10.0, 10.0, 10.0]):
            result = checks.estimate(1)
            assert result == (10.0, "down")

    def test_get_recent_weights_queries_newest_first(self):
        with patch("src.checks.query") as mock_query:
            mock_query.return_value = [
                {"weight_kg": 14.5},
                {"weight_kg": 12.0},
            ]
            weights = checks.get_recent_weights(3, last_n=7)
            assert weights == [14.5, 12.0]
            sql = mock_query.call_args[0][0]
            assert "ORDER BY date DESC" in sql
            assert mock_query.call_args[0][1] == (3, 7)


# --- reports routes ----------------------------------------------------------


class TestReportsRoutes:
    def test_index_redirects_when_not_logged_in(self):
        _, client = make_client()
        resp = client.get("/reports/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    @patch("src.reports._farmers")
    @patch("src.reports._daily_report")
    @patch("src.reports.checks.estimate")
    def test_index_renders_daily_report(self, mock_estimate, mock_daily, mock_farmers):
        _, client = make_client()
        login(client)
        mock_farmers.return_value = [{"farmer_id": 1, "name": "R. Perera"}]
        mock_daily.return_value = [
            {"date": date(2026, 6, 15), "total_kg": 24.5, "entries": 3},
        ]
        mock_estimate.return_value = None

        resp = client.get("/reports/?month=2026-06")
        assert resp.status_code == 200
        assert b"Reports & Trend" in resp.data
        assert b"Daily report" in resp.data
        assert b"24.50" in resp.data

    @patch("src.reports._farmers")
    @patch("src.reports._daily_report")
    @patch("src.reports.checks.estimate")
    def test_index_shows_trend_for_selected_farmer(
        self, mock_estimate, mock_daily, mock_farmers
    ):
        _, client = make_client()
        login(client)
        mock_farmers.return_value = [{"farmer_id": 1, "name": "R. Perera"}]
        mock_daily.return_value = []
        mock_estimate.return_value = (12.4, "up")

        resp = client.get("/reports/?month=2026-06&farmer_id=1")
        assert resp.status_code == 200
        assert b"Trend" in resp.data
        assert b"12.4" in resp.data
        assert b"up" in resp.data

    @patch("src.reports.query")
    @patch("src.reports._farmer_records")
    @patch("src.reports._farmers")
    @patch("src.reports.checks.estimate")
    def test_farmer_view_shows_records_and_trend(
        self, mock_estimate, mock_farmers, mock_records, mock_query
    ):
        _, client = make_client()
        login(client)
        
       
        def query_side_effect(sql, *args, **kwargs):
            if "SELECT farmer_id, name" in sql:
               
                return {"farmer_id": 1, "name": "R. Perera"}
            
            return [{"date": date(2026, 6, 10), "total_kg": 11.5, "entries": 1}]
            
        mock_query.side_effect = query_side_effect
        
        mock_records.return_value = [
            {"record_id": 1, "date": date(2026, 6, 10), "weight_kg": 11.5, "flagged": 0},
        ]
        mock_farmers.return_value = [{"farmer_id": 1, "name": "R. Perera"}]
        mock_estimate.return_value = (12.0, "down")

        resp = client.get("/reports/farmer/1?month=2026-06")
        
        
        assert resp.status_code == 200

    @patch("src.reports.query")
    def test_farmer_view_404_for_unknown_farmer(self, mock_query):
        _, client = make_client()
        login(client)
        mock_query.return_value = None

        resp = client.get("/reports/farmer/999")
        assert resp.status_code == 404

    @patch("src.reports._farmers")
    @patch("src.reports._daily_report")
    def test_charts_page_renders(self, mock_daily, mock_farmers):
        _, client = make_client()
        login(client)
        mock_farmers.return_value = []
        mock_daily.return_value = [
            {"date": date(2026, 6, 1), "total_kg": 10.0, "entries": 1},
        ]

        resp = client.get("/reports/charts?month=2026-06")
        assert resp.status_code == 200
        assert b"Collection charts" in resp.data
        assert b"chart.js" in resp.data.lower()

    @patch("src.reports._daily_report")
    def test_api_daily_returns_json(self, mock_daily):
        _, client = make_client()
        login(client)
        mock_daily.return_value = [
            {"date": date(2026, 6, 1), "total_kg": 10.0, "entries": 2},
        ]

        resp = client.get("/reports/api/daily?month=2026-06")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["values"] == [10.0]
        assert data["rows"][0]["entries"] == 2
