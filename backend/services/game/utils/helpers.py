"""
Helper utilities for game logic.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class GameHelpers:
    """General game helper functions."""
    
    @staticmethod
    def generate_id(prefix: str = "id") -> str:
        """Generate a unique ID with prefix."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate Manhattan distance between two points."""
        return abs(x2 - x1) + abs(y2 - y1)
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as Indian currency."""
        return f"₹{amount:,.2f}"
    
    @staticmethod
    def format_time_ago(dt: datetime) -> str:
        """Format datetime as 'time ago' string."""
        now = datetime.utcnow()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp value between min and max."""
        return max(min_value, min(max_value, value))
    
    @staticmethod
    def percentage(value: float, total: float) -> float:
        """Calculate percentage."""
        if total == 0:
            return 0.0
        return (value / total) * 100
    
    @staticmethod
    def get_adjacent_positions(x: int, y: int) -> List[tuple]:
        """Get list of adjacent grid positions (4-directional)."""
        return [
            (x, y + 1),  # North
            (x + 1, y),  # East
            (x, y - 1),  # South
            (x - 1, y),  # West
        ]
    
    @staticmethod
    def is_valid_grid_position(x: int, y: int, max_size: int = 10) -> bool:
        """Check if position is within valid grid bounds."""
        return 0 <= x < max_size and 0 <= y < max_size
