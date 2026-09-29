from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response, status

from samokat.services._delivery_tracking_simulation import (
    DeliveryTrackingSimulationService,
)

router = APIRouter(
    prefix="/delivery-tracking",
    route_class=DishkaRoute,
    tags=["Симуляция GPS данных курьеров"],
)


@router.post("/simulate", status_code=status.HTTP_204_NO_CONTENT)
async def simulate_delivery_tracking(
    service: FromDishka[DeliveryTrackingSimulationService],
) -> Response:
    await service.run_simulation()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
