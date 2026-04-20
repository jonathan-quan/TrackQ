from types import SimpleNamespace

from crud import _evaluate_leg_status, _roll_up_parlay_status


def leg(status):
    return SimpleNamespace(status=status)


def test_pending_when_actual_is_none():
    assert _evaluate_leg_status(None, 24.5, "over") == "pending"
    assert _evaluate_leg_status(None, 24.5, "under") == "pending"


def test_over_hit_and_miss():
    assert _evaluate_leg_status(25.0, 24.5, "over") == "hit"
    assert _evaluate_leg_status(24.0, 24.5, "over") == "miss"


def test_under_hit_and_miss():
    assert _evaluate_leg_status(24.0, 24.5, "under") == "hit"
    assert _evaluate_leg_status(25.0, 24.5, "under") == "miss"


def test_exact_line_is_miss_both_directions():
    assert _evaluate_leg_status(24.5, 24.5, "over") == "miss"
    assert _evaluate_leg_status(24.5, 24.5, "under") == "miss"


def test_parlay_hits_only_when_all_legs_hit():
    assert _roll_up_parlay_status([leg("hit"), leg("hit")]) == "hit"


def test_parlay_misses_if_any_leg_misses():
    assert _roll_up_parlay_status([leg("hit"), leg("miss"), leg("pending")]) == "miss"


def test_parlay_pending_if_any_leg_pending_and_none_miss():
    assert _roll_up_parlay_status([leg("hit"), leg("pending")]) == "pending"


def test_empty_parlay_is_pending():
    assert _roll_up_parlay_status([]) == "pending"
