"""In-process WebSocket broadcaster for display-only competitive events."""
import asyncio
from collections import defaultdict
from typing import DefaultDict, Set

from fastapi import WebSocket

from services.game.controllers.leaderboard_controller import LeaderboardController


class RealtimeEventHub:
    """Manages topic subscriptions for this Game Service process.

    Production deployments with multiple Game Service instances must replace this
    in-memory hub with a shared broker (for example Redis pub/sub).
    """

    LEADERBOARD_TOPIC = "leaderboard"

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._leaderboard_broadcast_task: asyncio.Task | None = None

    def subscribe(self, websocket: WebSocket, topic: str) -> bool:
        if topic != self.LEADERBOARD_TOPIC:
            return False
        self._subscribers[topic].add(websocket)
        return True

    def unsubscribe_all(self, websocket: WebSocket) -> None:
        for subscribers in self._subscribers.values():
            subscribers.discard(websocket)

    async def send_leaderboard_snapshot(self, websocket: WebSocket) -> None:
        """Send the current event leaderboard snapshot to a newly connected client."""
        event_leaderboard = await LeaderboardController.get_event_leaderboard()
        if event_leaderboard:
            await websocket.send_json({
                "type": "leaderboard.updated",
                **event_leaderboard
            })

    def schedule_leaderboard_broadcast(self) -> None:
        """Coalesce transaction bursts into one broadcast every two seconds."""
        if self._leaderboard_broadcast_task is None or self._leaderboard_broadcast_task.done():
            self._leaderboard_broadcast_task = asyncio.create_task(
                self._broadcast_after_delay()
            )

    async def _broadcast_after_delay(self) -> None:
        await asyncio.sleep(2)
        subscribers = list(self._subscribers[self.LEADERBOARD_TOPIC])
        if not subscribers:
            return

        event_leaderboard = await LeaderboardController.get_event_leaderboard()
        if not event_leaderboard:
            return

        payload = {"type": "leaderboard.updated", **event_leaderboard}
        for websocket in list(subscribers):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.unsubscribe_all(websocket)


realtime_event_hub = RealtimeEventHub()