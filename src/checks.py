"""Error/anomaly check + trend estimate (the 20-mark logic).

Owner: K.G.C. Ravishan (error check) and P.A.K.N. Dharmarathna (trend).

INTEGRATION STUB created by H.G.P.C. Sagara. This module is imported by
weights.py and reports.py rather than exposing its own routes. Implement the
two pure functions below exactly as specified in guideline §5.2 and §5.3 so
they are easy for QA to unit-test.
"""


def check(farmer_id, new_weight):
    """Error/anomaly check for a new weight (guideline §5.2).

    Expected behaviour to implement:
        IF new_weight <= 0:            return 'reject: must be positive'
        history = recent weights (last 10)
        IF len(history) < 3:           return 'ok'
        avg = average(history)
        IF new_weight > avg*3 or < avg/3: flag + return 'warn: please confirm'
        return 'ok'
    """
    raise NotImplementedError("Owner: K.G.C. Ravishan — implement per §5.2")


def estimate(farmer_id):
    """Moving-average trend estimate (guideline §5.3).

    Returns (round(moving_avg, 2), 'up'|'down') or None when fewer than 3
    records exist.
    """
    raise NotImplementedError("Owner: P.A.K.N. Dharmarathna — implement per §5.3")
