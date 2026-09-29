from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.websockets import WebSocket

from delivery_analytics.infrastructure.websocket.manager import (
    WebsocketManager,
    send_messages_to_client,
)

courier_events_router = APIRouter(tags=["Вебсокет: Местоположения курьеров"])


@courier_events_router.websocket("/ws/courier_events")
@inject
async def get_courier_events(
    ws: WebSocket,
    ws_manager: FromDishka[WebsocketManager],
):
    async with ws_manager.connect(ws) as client:
        await send_messages_to_client(client)
