from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    parlays = relationship("Parlay", back_populates="user", cascade="all, delete-orphan")


class Parlay(Base):
    __tablename__ = "parlays"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    game_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    status = Column(String(10), default="pending", nullable=False)  # pending / hit / miss
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="parlays")
    legs = relationship("ParlayLeg", back_populates="parlay", cascade="all, delete-orphan")


class ParlayLeg(Base):
    __tablename__ = "parlay_legs"

    id = Column(Integer, primary_key=True, index=True)
    parlay_id = Column(Integer, ForeignKey("parlays.id", ondelete="CASCADE"), nullable=False)
    player_name = Column(String(100), nullable=False)
    player_id = Column(Integer, nullable=False)
    stat_type = Column(String(20), nullable=False)  # points / rebounds / assists / steals / blocks / threes_made
    line = Column(Float, nullable=False)
    over_under = Column(String(5), nullable=False)  # over / under
    actual_value = Column(Float, nullable=True)
    status = Column(String(10), default="pending", nullable=False)  # pending / hit / miss

    parlay = relationship("Parlay", back_populates="legs")
