from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional
import uuid
from beanie import Document
from enum import Enum

class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"

class FranchiseEvent(Document):
    """A limited-time competitive event where players compete for a franchise."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    franchise_name: str = Field(..., description="Name of the franchise (e.g., Starbucks)")
    status: EventStatus = Field(default=EventStatus.UPCOMING)
    start_time: datetime
    end_time: datetime
    entry_fee: float = Field(..., ge=0)
    max_winners: int = Field(default=10, ge=1)
    
    # Track participants and their score during this event
    # Dict mapping player_id to their event revenue
    participants: Dict[str, float] = Field(default_factory=dict)
    
    class Settings:
        name = "franchise_events"
        
class EventCreate(BaseModel):
    franchise_name: str
    duration_minutes: int
    entry_fee: float
    max_winners: int = 10

class EventResponse(BaseModel):
    event_id: str
    franchise_name: str
    status: str
    start_time: datetime
    end_time: datetime
    entry_fee: float
    max_winners: int
    is_registered: bool = False
    participant_count: int = 0
