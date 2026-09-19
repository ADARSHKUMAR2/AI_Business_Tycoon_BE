"""
Trash item model for the store cleanliness system (Phase 3).
"""
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TrashItem(BaseModel):
    """Represents a single piece of trash on the store floor."""
    trash_id:   str      = Field(default_factory=lambda: f"trash_{uuid.uuid4().hex[:8]}")
    position_x: float    = Field(..., description="World X position where trash was dropped")
    position_y: float    = Field(..., description="World Y position where trash was dropped")
    dropped_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "example": {
                "trash_id":   "trash_a1b2c3d4",
                "position_x": 145.5,
                "position_y": 230.0,
                "dropped_at": "2026-09-18T10:00:00Z"
            }
        }
    }


class SpawnTrashRequest(BaseModel):
    """Request body for spawning a trash item (sent by Godot client)."""
    position_x: float = Field(..., description="World X position")
    position_y: float = Field(..., description="World Y position")

    model_config = {
        "json_schema_extra": {
            "example": {
                "position_x": 145.5,
                "position_y": 230.0
            }
        }
    }
