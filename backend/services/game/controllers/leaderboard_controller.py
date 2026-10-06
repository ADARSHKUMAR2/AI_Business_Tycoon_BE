"""Read-only competitive leaderboard calculations from persisted player state."""
from datetime import datetime, timedelta
from typing import List, Optional

from services.game.models.leaderboard import LeaderboardEntry, LeaderboardResponse
from services.game.models.player import PlayerState


class LeaderboardController:
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100

    @staticmethod
    async def get_leaderboard(metric: str, limit: int = DEFAULT_LIMIT) -> LeaderboardResponse:
        if metric not in ("net-worth", "revenue", "customers-served"):
            raise ValueError(f"Unsupported leaderboard metric: {metric}")

        bounded_limit = max(1, min(limit, LeaderboardController.MAX_LIMIT))
        players: List[PlayerState] = await PlayerState.find_all().to_list()

        def get_value(player: PlayerState) -> float:
            if metric == "net-worth":
                return float(player.calculate_net_worth())
            if metric == "revenue":
                return float(sum(business.stats.total_revenue for business in player.businesses))
            return float(sum(business.stats.total_customers_served for business in player.businesses))

        ranked_players = sorted(players, key=get_value, reverse=True)[:bounded_limit]
        entries = [
            LeaderboardEntry(
                rank=index + 1,
                player_id=player.player_id,
                display_name=player.name,
                value=get_value(player),
            )
            for index, player in enumerate(ranked_players)
        ]

        return LeaderboardResponse(
            metric=metric,
            updated_at=datetime.utcnow(),
            entries=entries,
        )

    @staticmethod
    async def get_event_leaderboard() -> Optional[dict]:
        """
        Fetch the active (or recently completed) FranchiseEvent and
        return a leaderboard dict formatted exactly as Unity expects:
        {
            "event_id": "evt_xxx",
            "franchise_name": "Starbucks",
            "time_remaining_seconds": 1500,
            "entries": [
                {"rank": 1, "player_id": "p_xxx", "display_name": "Adarsh", "value": 5000.0}
            ]
        }
        Returns None if no active or recent event exists.
        """
        from services.game.models.events import FranchiseEvent, EventStatus
        from services.game.utils.state_manager import state_manager

        now = datetime.utcnow()
        grace_cutoff = now - timedelta(hours=24)

        # Priority 1: active or upcoming event
        db_event = await FranchiseEvent.find_one(
            {"status": {"$in": [EventStatus.UPCOMING, EventStatus.ACTIVE]}}
        )

        # Priority 2: recently completed event (grace period)
        if not db_event:
            db_event = await FranchiseEvent.find_one(
                {"status": EventStatus.COMPLETED, "end_time": {"$gte": grace_cutoff}},
                sort=[("end_time", -1)]
            )

        if not db_event:
            return None

        # Calculate time remaining (0 when completed)
        time_remaining = 0
        if db_event.status != EventStatus.COMPLETED:
            time_remaining = max(0, int((db_event.end_time - now).total_seconds()))

        # Sort participants by revenue descending
        sorted_participants = sorted(
            db_event.participants.items(), key=lambda x: x[1], reverse=True
        )

        entries = []
        for rank, (player_id, score) in enumerate(sorted_participants, start=1):
            try:
                player = await state_manager.load_player(player_id)
                display_name = player.name
            except Exception:
                display_name = "Unknown Player"

            entries.append({
                "rank": rank,
                "player_id": player_id,
                "display_name": display_name,
                "value": float(score),
            })

        return {
            "event_id": db_event.event_id,
            "franchise_name": db_event.franchise_name,
            "time_remaining_seconds": time_remaining,
            "entries": entries,
        }
