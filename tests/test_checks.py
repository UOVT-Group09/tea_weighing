"""Unit tests for src/checks.py — the anomaly check (§5.2) and trend estimate (§5.3).

Owner of the module under test: K.G.C. Ravishan (check) / P.A.K.N. Dharmarathna
(get_recent_weights / estimate).

These are pure unit tests: ``checks.query`` is monkeypatched so no real MySQL
connection is needed to run them.
"""

import pytest

from src import checks


def _rows(*weights):
    """Build fake ``db.query`` rows in the shape checks.py expects."""
    return [{"weight_kg": w} for w in weights]


def _boom(*_args, **_kwargs):
    raise AssertionError("query() should not have been called")


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_weight", [0, -1, -12.5])
def test_check_rejects_zero_or_negative_weight_without_hitting_db(monkeypatch, bad_weight):
    monkeypatch.setattr(checks, "query", _boom)
    assert checks.check(1, bad_weight) == checks.REJECT_NOT_POSITIVE


def test_check_rejects_none_weight_without_hitting_db(monkeypatch):
    monkeypatch.setattr(checks, "query", _boom)
    assert checks.check(1, None) == checks.REJECT_NOT_POSITIVE


@pytest.mark.parametrize("history_len", [0, 1, 2])
def test_check_is_ok_when_fewer_than_three_history_rows(monkeypatch, history_len):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(*([12.0] * history_len)))
    assert checks.check(1, 90.0) == checks.OK


def test_check_ok_when_weight_within_range(monkeypatch):
    # avg = 12.375, range is (avg/3, avg*3) = (~4.1, ~37.1)
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(11.8, 13.2, 12.0, 12.5))
    assert checks.check(1, 20.0) == checks.OK


def test_check_warns_when_far_above_average(monkeypatch):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(11.8, 13.2, 12.0, 12.5))
    assert checks.check(1, 90.0) == checks.WARN_OUT_OF_RANGE


def test_check_warns_when_far_below_average(monkeypatch):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(11.8, 13.2, 12.0, 12.5))
    assert checks.check(1, 1.0) == checks.WARN_OUT_OF_RANGE


def test_check_boundary_values_are_ok_not_warn(monkeypatch):
    # avg = 10 exactly -> the boundary itself (avg*3, avg/3) must NOT warn
    # since checks.py uses strict > / < comparisons.
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(10, 10, 10, 10))
    assert checks.check(1, 30.0) == checks.OK
    assert checks.check(1, 10 / 3) == checks.OK


def test_check_queries_history_scoped_to_farmer_with_limit(monkeypatch):
    seen = {}

    def fake_query(sql, params=None, **_kwargs):
        seen["sql"] = sql
        seen["params"] = params
        return _rows(11.8, 13.2, 12.0, 12.5)

    monkeypatch.setattr(checks, "query", fake_query)
    checks.check(42, 12.0)

    assert seen["params"] == (42, checks.HISTORY_LIMIT)
    assert "weight_record" in seen["sql"]
    assert "farmer_id" in seen["sql"]


# ---------------------------------------------------------------------------
# get_recent_weights()
# ---------------------------------------------------------------------------


def test_get_recent_weights_returns_floats_in_db_order(monkeypatch):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(13.2, 11.8, 12.0))
    assert checks.get_recent_weights(1) == [13.2, 11.8, 12.0]


def test_get_recent_weights_passes_last_n_as_the_limit(monkeypatch):
    seen = {}

    def fake_query(sql, params=None, **_kwargs):
        seen["params"] = params
        return []

    monkeypatch.setattr(checks, "query", fake_query)
    checks.get_recent_weights(7, last_n=5)

    assert seen["params"] == (7, 5)


def test_get_recent_weights_empty_history_returns_empty_list(monkeypatch):
    monkeypatch.setattr(checks, "query", lambda *a, **k: [])
    assert checks.get_recent_weights(1) == []


# ---------------------------------------------------------------------------
# estimate()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("history_len", [0, 1, 2])
def test_estimate_is_none_when_fewer_than_three_records(monkeypatch, history_len):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(*([12.0] * history_len)))
    assert checks.estimate(1) is None


def test_estimate_trend_up_when_latest_above_moving_average(monkeypatch):
    # newest-first history: latest=15, avg(15,10,10,10,10)=11.0 -> up
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(15, 10, 10, 10, 10))
    moving_avg, trend = checks.estimate(1)
    assert trend == "up"
    assert moving_avg == pytest.approx(11.0)


def test_estimate_trend_down_when_latest_below_moving_average(monkeypatch):
    # newest-first history: latest=5, avg(5,10,10,10,10)=9.0 -> down
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(5, 10, 10, 10, 10))
    moving_avg, trend = checks.estimate(1)
    assert trend == "down"
    assert moving_avg == pytest.approx(9.0)


def test_estimate_rounds_moving_average_to_two_decimal_places(monkeypatch):
    monkeypatch.setattr(checks, "query", lambda *a, **k: _rows(10, 10, 10, 11))
    moving_avg, _trend = checks.estimate(1)
    assert moving_avg == round(41 / 4, 2)


def test_estimate_only_looks_at_last_seven_records(monkeypatch):
    seen = {}

    def fake_query(sql, params=None, **_kwargs):
        seen["params"] = params
        return _rows(10, 10, 10)

    monkeypatch.setattr(checks, "query", fake_query)
    checks.estimate(1)

    assert seen["params"] == (1, 7)
