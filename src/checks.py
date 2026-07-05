"""Error/anomaly check + trend estimate (the 20-mark logic).

Owner: K.G.C. Ravishan (error check) and P.A.K.N. Dharmarathna (trend).

This module is imported by weights.py and reports.py rather than exposing its
own routes, so the two functions below are plain, easy-to-unit-test Python —
no Flask request/response objects involved.
"""

from .db import query

REJECT_NOT_POSITIVE = "reject: must be positive"
WARN_OUT_OF_RANGE = "warn: please confirm"
OK = "ok"

HISTORY_LIMIT = 10
MIN_HISTORY_FOR_RANGE_CHECK = 3
RANGE_MULTIPLIER = 3


def check(farmer_id, new_weight):
    """Error/anomaly check for a new weight (guideline §5.2).

        IF new_weight <= 0:            return 'reject: must be positive'
        history = recent weights (last 10)
        IF len(history) < 3:           return 'ok'
        avg = average(history)
        IF new_weight > avg*3 or < avg/3: flag + return 'warn: please confirm'
        return 'ok'
    """
    if new_weight is None or new_weight <= 0:
        return REJECT_NOT_POSITIVE

    rows = query(
        """
        SELECT weight_kg FROM weight_record
        WHERE farmer_id = %s
        ORDER BY date DESC, record_id DESC
        LIMIT %s
        """,
        (farmer_id, HISTORY_LIMIT),
    )
    history = [float(row["weight_kg"]) for row in rows]

    if len(history) < MIN_HISTORY_FOR_RANGE_CHECK:
        return OK

    avg = sum(history) / len(history)
    if new_weight > avg * RANGE_MULTIPLIER or new_weight < avg / RANGE_MULTIPLIER:
        return WARN_OUT_OF_RANGE

    return OK


def get_recent_weights(farmer_id, last_n=7):
    """Return the most recent weight values for a farmer (newest first)."""
    rows = query(
        """
        SELECT weight_kg FROM weight_record
        WHERE farmer_id = %s
        ORDER BY date DESC, record_id DESC
        LIMIT %s
        """,
        (farmer_id, last_n),
    )
    return [float(row["weight_kg"]) for row in rows]


def estimate(farmer_id):
    """Moving-average trend estimate (guideline §5.3).

    Returns (round(moving_avg, 2), 'up'|'down') or None when fewer than 3
    records exist.
    """
    history = get_recent_weights(farmer_id, last_n=7)
    if len(history) < 3:
        return None

    moving_avg = sum(history) / len(history)
    latest = history[0]
    trend = "up" if latest > moving_avg else "down"
    return (round(moving_avg, 2), trend)
