from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

StatType = Literal["points", "rebounds", "assists", "steals", "blocks", "threes_made"]
OverUnder = Literal["over", "under"]


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
    player_name: str = Field(min_length=1, max_length=100)
    player_id: int
    stat_type: StatType
    line: float = Field(ge=0)
    over_under: OverUnder


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
    matchup: Optional[str] = None


# ---------- Parlay ----------
class ParlayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    game_date: str  # YYYY-MM-DD

    @field_validator("game_date")
    @classmethod
    def validate_game_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("game_date must be in YYYY-MM-DD format")
        return v


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


# ---------- Search ----------
class PlayerSearchResult(BaseModel):
    player_id: int
    full_name: str
