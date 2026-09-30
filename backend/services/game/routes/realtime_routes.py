import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.game.services.realtime_event_hub import realtime_event_hub


router = APIRouter(tags=["Realtime Events"])


@router.websocket("/events/leaderboard")
async def leaderboard_events(websocket: WebSocket):
    """Display-only leaderboard event stream for connected Unity clients."""
    await websocket.accept()
    try:
        while True:
            message = json.loads(await websocket.receive_text())
            if message.get("type") != "subscribe":
                await websocket.send_json({"type": "error", "message": "Expected subscribe message."})
                continue

            subscribed = []
            for topic in message.get("topics", []):
                if realtime_event_hub.subscribe(websocket, topic):
                    subscribed.append(topic)

            await websocket.send_json({"type": "subscribed", "topics": subscribed})
            if realtime_event_hub.LEADERBOARD_TOPIC in subscribed:
                await realtime_event_hub.send_leaderboard_snapshot(websocket)
    except (WebSocketDisconnect, json.JSONDecodeError):
        pass
    finally:
        realtime_event_hub.unsubscribe_all(websocket)