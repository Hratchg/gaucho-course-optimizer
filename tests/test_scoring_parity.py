"""TEST-1: API scoring must stay within rounding of the frontend formula.

The API rounds to 2 decimals (compute_gaucho_score). The React client uses
Math.round (integer). Equal 0.25 weights — the default toggle set — must
agree within 1 point.
"""

from etl.scoring import compute_gaucho_score


def js_round(value: float) -> int:
    """Math.round — half away from zero — not Python 3 banker's rounding."""
    import math
    return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))


def frontend_equal_weight_score(
    gpa: float, quality: float, difficulty: float, sentiment: float
) -> int:
    """Mirror frontend/src/lib/scoring.ts computeGauchoScore with all toggles on."""
    raw = gpa * 0.25 + quality * 0.25 + difficulty * 0.25 + sentiment * 0.25
    return js_round(max(0.0, min(100.0, raw * 100)))


def test_equal_weight_parity_known_inputs():
    cases = [
        (0.5, 0.5, 0.5, 0.5),
        (1.0, 1.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 0.0),
        (0.8, 0.7, 0.6, 0.5),
        (0.88, 0.84, 0.38, 0.825),
        (0.81, 0.73, 0.62, 0.54),
    ]
    for factors in cases:
        api = compute_gaucho_score(*factors)
        frontend = frontend_equal_weight_score(*factors)
        assert abs(api - frontend) <= 1, (factors, api, frontend)
