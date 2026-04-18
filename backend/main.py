import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from models import User
import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from services import nba_service
import crud
import scheduler

Base.metadata.create_all(bind=engine)


def _attach_matchups(parlay: "models.Parlay") -> None:
    """Populate a transient `.matchup` attr on each leg so LegOut serializes it.

    Runs lookups in parallel because each call may hit nba.com on a cold
    cache (CommonPlayerInfo for the player's team_id). After the first hit
    everything is in-memory cached.
    """
    legs = list(parlay.legs)
    if not legs:
        return

    # Warm the shared scoreboard cache once before fanning out.
    nba_service.get_games_on_date(parlay.game_date)

    def _matchup_for(leg) -> str | None:
        return nba_service.get_matchup_for_player(leg.player_id, parlay.game_date)

    max_workers = min(8, max(1, len(legs)))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        matchups = list(ex.map(_matchup_for, legs))

    for leg, matchup in zip(legs, matchups):
        leg.matchup = matchup


app = FastAPI(title="TrackQ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _start_background_tasks():
    scheduler.set_main_loop(asyncio.get_running_loop())
    await scheduler.start_all_pending()


@app.get("/")
def root():
    return {"status": "ok", "app": "TrackQ"}


# ---------- Auth ----------
@app.post(
    "/auth/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter((User.email == payload.email) | (User.username == payload.username))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses `username` for the identifier field;
    # we treat that field as the user's email.
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=str(user.id))
    return schemas.Token(access_token=token)


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------- Parlays ----------
@app.post(
    "/parlays",
    response_model=schemas.ParlayOut,
    status_code=status.HTTP_201_CREATED,
)
def create_parlay(
    payload: schemas.ParlayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parlay = crud.create_parlay(
        db, user_id=current_user.id, name=payload.name, game_date=payload.game_date
    )
    scheduler.start_parlay_task(parlay.id)
    return parlay


@app.get("/parlays", response_model=list[schemas.ParlayOut])
def list_parlays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.list_parlays(db, user_id=current_user.id)


@app.get("/parlays/{parlay_id}", response_model=schemas.ParlayDetail)
def get_parlay(
    parlay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parlay = crud.get_parlay(db, parlay_id=parlay_id, user_id=current_user.id)
    if not parlay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlay not found")
    # Note: we deliberately do NOT call _attach_matchups here. Matchup strings
    # require live nba.com lookups (CommonPlayerInfo per player), so attaching
    # them on every GET makes the detail page block on the network for several
    # seconds on a cold cache. The refresh endpoint attaches them, and the
    # frontend triggers a refresh right after loading the parlay.
    return parlay


@app.delete("/parlays/{parlay_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parlay(
    parlay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parlay = crud.get_parlay(db, parlay_id=parlay_id, user_id=current_user.id)
    if not parlay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlay not found")
    crud.delete_parlay(db, parlay)
    scheduler.cancel_parlay_task(parlay_id)


@app.post("/parlays/{parlay_id}/refresh", response_model=schemas.ParlayDetail)
def refresh_parlay(
    parlay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parlay = crud.get_parlay(db, parlay_id=parlay_id, user_id=current_user.id)
    if not parlay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlay not found")
    # nba_api is blocking — offload to a thread so we don't stall the event loop
    crud.refresh_parlay(db, parlay)
    db.refresh(parlay)
    _attach_matchups(parlay)
    return parlay


# ---------- Legs ----------
@app.post(
    "/parlays/{parlay_id}/legs",
    response_model=schemas.LegOut,
    status_code=status.HTTP_201_CREATED,
)
def add_leg(
    parlay_id: int,
    payload: schemas.LegCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parlay = crud.get_parlay(db, parlay_id=parlay_id, user_id=current_user.id)
    if not parlay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlay not found")
    leg = crud.add_leg(
        db,
        parlay_id=parlay.id,
        player_name=payload.player_name,
        player_id=payload.player_id,
        stat_type=payload.stat_type,
        line=payload.line,
        over_under=payload.over_under,
    )
    leg.matchup = nba_service.get_matchup_for_player(leg.player_id, parlay.game_date)
    return leg


@app.delete("/legs/{leg_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leg(
    leg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leg = crud.get_leg(db, leg_id=leg_id, user_id=current_user.id)
    if not leg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leg not found")
    crud.delete_leg(db, leg)


# ---------- Search ----------
@app.get("/search/nba", response_model=list[schemas.PlayerSearchResult])
def search_nba(
    name: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    return nba_service.search_players(name, limit=limit)
