from delivery_analytics.infrastructure.websocket.manager import WebsocketManager


class WebsocketGPSBroadcaster:
    def __init__(self, ws_manager: WebsocketManager):
        self.ws_manager = ws_manager

    async def broadcast_courier_tracking_events(self, events: list[dict]):
        events = [
            {
                **event,
                "recorded_at": event["recorded_at"].isoformat(),
            } for event in events
        ]
        await self.ws_manager.broadcast({
            "type": "couriers_snapshot",
            "items": events,
        })
