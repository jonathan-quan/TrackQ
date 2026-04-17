from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- User ----------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Parlay Leg ----------
class LegCreate(BaseModel):
    player_name: str
    player_id: int
    stat_type: str  # points / rebounds / assists / steals / blocks / threes_made
    line: float
    over_under: str  # over / under


class LegOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parlay_id: int
    player_name: str
    player_id: int
    stat_type: str
    line: float
    over_under: str
    actual_value: Optional[float] = None
    status: str


# ---------- Parlay ----------
class ParlayCreate(BaseModel):
    name: str
    game_date: str  # YYYY-MM-DD


class ParlayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    game_date: str
    status: str
    created_at: datetime


class ParlayDetail(ParlayOut):
    legs: List[LegOut] = []
