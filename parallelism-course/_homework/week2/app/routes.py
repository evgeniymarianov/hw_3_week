from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.event_cache import (
    EventCacheMissTimeout,
    EventNotFoundError,
    get_event_single_flight,
)

from fastapi import APIRouter, Depends, Header, status

from app.schemas import (
    BookingCreate,
    CheckoutResponse,
    EventCreate,
    EventDashboard,
    EventRead,
    EventSeatRead,
    LocationDetail,
    LocationRead,
    PaymentCompleted,
    PaymentCreate,
    SeatRead,
)

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from app.views import ViewService

router = APIRouter()


def get_current_user_id(x_user_id: Annotated[int, Header()]) -> int:
    return x_user_id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]


def get_view_service() -> ViewService:
    return ViewService()


ViewServiceProvider = Annotated[ViewService, Depends(get_view_service)]


@router.get("/locations")
async def list_locations() -> list[LocationRead]:
    """Возвращает список площадок."""
    ...


@router.get("/locations/{location_id}")
async def get_location(location_id: int) -> LocationDetail:
    """Возвращает площадку со схемой мест."""
    ...


@router.get("/locations/{location_id}/seats")
async def list_location_seats(location_id: int) -> list[SeatRead]:
    """Возвращает все места площадки."""
    ...


@router.get("/events")
async def list_events() -> list[EventRead]:
    """Возвращает список мероприятий для клиента."""
    ...


@router.get("/events/{event_id}")
async def get_event(
    event_id: int,
    request: Request,
    service: ViewServiceProvider,
) -> EventRead:
    """Возвращает описание мероприятия.

    Распределённый SingleFlight: при одновременном cache miss в БД за событием
    пойдёт только один запрос (под Redis Lock), остальные дождутся результата
    из Redis-кэша либо упадут по таймауту с 503.

    Учёт просмотров: просмотр того же мероприятия с того же IP засчитывается
    не чаще одного раза за 5 минут (дедупликация через Redis). Уникальные
    просмотры уходят в asyncio.Queue и пишутся в БД фоновым воркером
    агрегированным обновлением счётчика.
    """
    await service.register_view(event_id=event_id, ip=request.client.host if request.client else None)

    try:
        return await get_event_single_flight(event_id)
    except EventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Мероприятие {event_id} не найдено",
        ) from None
    except EventCacheMissTimeout:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось дождаться загрузки мероприятия, повторите запрос позже",
        ) from None


@router.get("/events/{event_id}/seats")
async def list_event_seats(event_id: int) -> list[EventSeatRead]:
    """Возвращает места на мероприятии с ценами и статусами."""
    ...


@router.get("/organizer/events")
async def list_organizer_events(organizer_id: CurrentUserId) -> list[EventRead]:
    """Возвращает список созданных событий текущего организатора."""
    ...


@router.post("/organizer/events")
async def create_event(payload: EventCreate, organizer_id: CurrentUserId) -> EventRead:
    """Создает мероприятие от лица текущего организатора."""
    ...


@router.get("/organizer/events/{event_id}/dashboard")
async def get_event_dashboard(event_id: int, organizer_id: CurrentUserId) -> EventDashboard:
    """Возвращает аналитические данные для дашборда по мероприятию."""
    # TODO: проверить, что мероприятие принадлежит organizer_id.
    # TODO: конкурентно загрузить аналитику продаж и занятость мест отдельными запросами к БД.
    ...


@router.post("/events/{event_id}/checkout")
async def prepare_checkout(
    event_id: int,
    payload: BookingCreate,
    user_id: CurrentUserId,
) -> CheckoutResponse:
    """Временно бронирует места за клиентом, возвращает итоговую стоимость
        и возможность страховки."""
    # TODO: создать бронь для выбранных мест через SELECT FOR UPDATE, и посчитать базовую стоимость.
    # TODO: конкурентно запросить Payment API и Protection API для расчета checkout.
    ...


@router.post("/bookings/{booking_id}/pay")
async def pay_booking(
    booking_id: int,
    payload: PaymentCreate,
    user_id: CurrentUserId,
) -> PaymentCompleted:
    """Принимает способ оплаты и флаг with_protection."""
    ...
