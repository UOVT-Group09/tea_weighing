from src.validators import parse_weight, parse_past_or_today
from datetime import date


# =========================
# WEIGHT VALIDATION TESTS
# =========================
def test_parse_weight_valid():
    value, err = parse_weight("10")
    assert value == 10.0
    assert err is None


def test_parse_weight_negative():
    value, err = parse_weight("-5")
    assert value is None
    assert err == "Weight must be positive."


def test_parse_weight_invalid():
    value, err = parse_weight("abc")
    assert value is None
    assert err == "Weight must be a number."


def test_parse_weight_zero():
    value, err = parse_weight("0")
    assert value is None
    assert err == "Weight must be positive."


# =========================
# DATE VALIDATION TESTS
# =========================
def test_parse_date_valid():
    today = date.today().isoformat()
    value, err = parse_past_or_today(today)

    assert err is None
    assert value.isoformat() == today


def test_parse_date_invalid_format():
    value, err = parse_past_or_today("2026/01/01")

    assert value is None
    assert err == "Invalid date format."


def test_parse_future_date():
    future = "2099-01-01"
    value, err = parse_past_or_today(future)

    assert value is None
    assert err == "Future dates are not allowed."