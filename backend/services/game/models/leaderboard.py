"""Contracts for competitive leaderboard snapshots and real-time events."""
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


LeaderboardMetric = Literal["net-worth", "revenue", "customers-served"]


class LeaderboardEntry(BaseModel):
    rank: int = Field(..., ge=1)
    player_id: str
    display_name: str
    value: float = Field(..., ge=0)


class LeaderboardResponse(BaseModel):
    metric: LeaderboardMetric
    updated_at: datetime
    entries: List[LeaderboardEntry]
