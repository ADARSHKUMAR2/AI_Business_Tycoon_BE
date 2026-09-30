"""Read-only competitive leaderboard calculations from persisted player state."""
from datetime import datetime
from typing import List

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