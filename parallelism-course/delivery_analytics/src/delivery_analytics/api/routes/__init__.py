from fastapi import APIRouter

from delivery_analytics.api.routes.ws_courier_events import courier_events_router

__all__ = ("main_router",)


main_router = APIRouter()
main_router.include_router(courier_events_router)
