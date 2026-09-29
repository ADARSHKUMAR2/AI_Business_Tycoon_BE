"""Server-authoritative world time and weather contract."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WorldStateResponse(BaseModel):
    """Current shared world conditions returned to Unity clients."""

    time_of_day: Literal["day", "night"]
    weather: Literal["clear", "rain"]
    state_started_at: datetime
    next_time_change_at: datetime
    next_weather_change_at: datetime
    rain_spawn_multiplier: float = Field(..., gt=0)
    night_spawn_multiplier: float = Field(..., gt=0)