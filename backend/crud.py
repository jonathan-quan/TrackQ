from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from models import Parlay, ParlayLeg
from services import nba_service


# ---------- Parlays ----------
def create_parlay(db: Session, user_id: int, name: str, game_date: str) -> Parlay:
    parlay = Parlay(user_id=user_id, name=name, game_date=game_date, status="pending")
    db.add(parlay)
    db.commit()
    db.refresh(parlay)
    return parlay


def list_parlays(db: Session, user_id: int) -> List[Parlay]:
    return (
        db.query(Parlay)
        .filter(Parlay.user_id == user_id)
        .order_by(Parlay.created_at.desc())
        .all()
    )


def get_parlay(db: Session, parlay_id: int, user_id: int) -> Optional[Parlay]:
    """Fetch a parlay only if it belongs to the given user."""
    return (
        db.query(Parlay)
        .filter(Parlay.id == parlay_id, Parlay.user_id == user_id)
        .first()
    )


def delete_parlay(db: Session, parlay: Parlay) -> None:
    db.delete(parlay)  # cascade deletes all legs
    db.commit()


# ---------- Legs ----------
def add_leg(
    db: Session,
    parlay_id: int,
    player_name: str,
    player_id: int,
    stat_type: str,
    line: float,
    over_under: str,
) -> ParlayLeg:
    leg = ParlayLeg(
        parlay_id=parlay_id,
        player_name=player_name,
        player_id=player_id,
        stat_type=stat_type,
        line=line,
        over_under=over_under,
        status="pending",
    )
    db.add(leg)
    db.commit()
    db.refresh(leg)
    return leg


def get_leg(db: Session, leg_id: int, user_id: int) -> Optional[ParlayLeg]:
    """Fetch a leg only if its parent parlay belongs to the given user."""
    return (
        db.query(ParlayLeg)
        .join(Parlay, Parlay.id == ParlayLeg.parlay_id)
        .filter(ParlayLeg.id == leg_id, Parlay.user_id == user_id)
        .first()
    )


def delete_leg(db: Session, leg: ParlayLeg) -> None:
    db.delete(leg)
    db.commit()


# ---------- Refresh / status logic ----------
def _evaluate_leg_status(actual: Optional[float], line: float, over_under: str) -> str:
    """Compute leg status given actual value. Returns pending/hit/miss."""
    if actual is None:
        return "pending"
    if over_under == "over":
        return "hit" if actual > line else "miss"
    return "hit" if actual < line else "miss"


def _roll_up_parlay_status(legs: List[ParlayLeg]) -> str:
    """Compute overall parlay status from leg statuses."""
    if any(l.status == "miss" for l in legs):
        return "miss"
    if legs and all(l.status == "hit" for l in legs):
        return "hit"
    return "pending"


def refresh_parlay(db: Session, parlay: Parlay) -> Parlay:
    """Fetch real stats for each leg and update leg + parlay status.

    For each leg:
      - Find the player's game on the parlay's game_date.
      - If that game is `scheduled`, leg stays pending.
      - If `live` or `final`, update `actual_value` from the box score.
      - If `final`, lock in hit/miss (treat DNP / None as 0).
      - If `live`, update actual_value but keep status=pending until final.

    Per-leg nba_api calls run in a thread pool so a single refresh doesn't
    take O(legs * network_latency) wall time.
    """
    game_date = parlay.game_date
    legs = list(parlay.legs)
    any_not_final = False

    if not legs:
        db.commit()
        db.refresh(parlay)
        return parlay

    # Warm the shared scoreboard cache once so the parallel workers below
    # don't each issue a duplicate ScoreboardV2 request.
    nba_service.get_games_on_date(game_date)

    def _fetch(leg: ParlayLeg) -> Tuple[Optional[float], str]:
        return nba_service.fetch_leg_update(leg.player_id, leg.stat_type, game_date)

    max_workers = min(8, max(1, len(legs)))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = list(ex.map(_fetch, legs))

    for leg, (actual, game_status) in zip(legs, results):
        if game_status == "none_found":
            any_not_final = True
            continue

        if game_status == "scheduled":
            any_not_final = True
            continue

        if game_status == "live":
            leg.actual_value = actual
            leg.status = "pending"
            any_not_final = True
            continue

        # final (or any unexpected status — treat as terminal so legs lock in)
        final_value = actual if actual is not None else 0.0
        leg.actual_value = final_value
        leg.status = _evaluate_leg_status(final_value, leg.line, leg.over_under)

    if any_not_final:
        parlay.status = "pending" if parlay.status == "pending" else parlay.status
        if not any(l.status == "miss" for l in parlay.legs):
            parlay.status = "pending"
        else:
            parlay.status = "miss"
    else:
        parlay.status = _roll_up_parlay_status(list(parlay.legs))

    db.commit()
    db.refresh(parlay)
    return parlay

