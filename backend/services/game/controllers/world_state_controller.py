"""Server-authoritative deterministic world time and weather controller."""

from datetime import datetime, timedelta

from services.game.models.world_state import WorldStateResponse


class WorldStateController:
    """Build the shared world state from UTC time without requiring persistence."""

    DAY_DURATION = timedelta(minutes=5)
    NIGHT_DURATION = timedelta(minutes=3)
    WEATHER_CHANGE_INTERVAL = timedelta(minutes=4)
    RAIN_SPAWN_MULTIPLIER = 0.75
    NIGHT_SPAWN_MULTIPLIER = 0.7
    EPOCH = datetime(2026, 1, 1)

    @classmethod
    def get_world_state(cls, now: datetime | None = None) -> WorldStateResponse:
        """Return the current shared state from server UTC time.

        The schedule is deterministic so all clients receive the same state and
        can recover correctly after reconnecting without local random rolls.
        """
        current = now or datetime.utcnow()
        elapsed_seconds = max(0, int((current - cls.EPOCH).total_seconds()))

        day_seconds = int(cls.DAY_DURATION.total_seconds())
        night_seconds = int(cls.NIGHT_DURATION.total_seconds())
        time_cycle_seconds = day_seconds + night_seconds
        time_cycle_offset = elapsed_seconds % time_cycle_seconds

        if time_cycle_offset < day_seconds:
            time_of_day = "day"
            state_started_at = current - timedelta(seconds=time_cycle_offset)
            next_time_change_at = state_started_at + cls.DAY_DURATION
        else:
            time_of_day = "night"
            night_offset = time_cycle_offset - day_seconds
            state_started_at = current - timedelta(seconds=night_offset)
            next_time_change_at = state_started_at + cls.NIGHT_DURATION

        weather_interval_seconds = int(cls.WEATHER_CHANGE_INTERVAL.total_seconds())
        weather_cycle = elapsed_seconds // weather_interval_seconds
        weather_offset = elapsed_seconds % weather_interval_seconds
        weather = "rain" if weather_cycle % 2 else "clear"
        next_weather_change_at = current + timedelta(seconds=weather_interval_seconds - weather_offset)

        return WorldStateResponse(
            time_of_day=time_of_day,
            weather=weather,
            state_started_at=state_started_at,
            next_time_change_at=next_time_change_at,
            next_weather_change_at=next_weather_change_at,
            rain_spawn_multiplier=cls.RAIN_SPAWN_MULTIPLIER,
            night_spawn_multiplier=cls.NIGHT_SPAWN_MULTIPLIER,
        )