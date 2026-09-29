import asyncio
import secrets
import hashlib
import random
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel


app = FastAPI(title="API Даркстора")

API_KEY = "drkstr-D7xR4nQ9vK2mP8sT5yB6"
MIN_DELAY_SECONDS = 0.03
MAX_DELAY_SECONDS = 0.07
SLOW_RESPONSE_PROBABILITY = 0.1
MIN_SLOW_DELAY_SECONDS = 1.0
MAX_SLOW_DELAY_SECONDS = 2.0
DARKSTORE_ASSORTMENT_PERCENT = 25
DARKSTORES = [
    {
        "id": "darkstore-palace",
        "address": "Санкт-Петербург, Дворцовая площадь, 2",
        "lat": 59.9398,
        "lon": 30.3146,
    },
    {
        "id": "darkstore-nevsky-28",
        "address": "Санкт-Петербург, Невский проспект, 28",
        "lat": 59.9359,
        "lon": 30.3259,
    },
    {
        "id": "darkstore-isaak",
        "address": "Санкт-Петербург, Исаакиевская площадь, 4",
        "lat": 59.9343,
        "lon": 30.3061,
    },
    {
        "id": "darkstore-kazan",
        "address": "Санкт-Петербург, Казанская площадь, 2",
        "lat": 59.9343,
        "lon": 30.3245,
    },
    {
        "id": "darkstore-petrograd",
        "address": "Санкт-Петербург, Петропавловская крепость, 3",
        "lat": 59.9500,
        "lon": 30.3167,
    },
    {
        "id": "darkstore-nevsky-85",
        "address": "Санкт-Петербург, Невский проспект, 85",
        "lat": 59.9297,
        "lon": 30.3627,
    },
    {
        "id": "darkstore-ligovsky",
        "address": "Санкт-Петербург, Лиговский проспект, 30А",
        "lat": 59.9275,
        "lon": 30.3609,
    },
    {
        "id": "darkstore-vasileostrovsky",
        "address": "Санкт-Петербург, Биржевая площадь, 4",
        "lat": 59.9443,
        "lon": 30.3061,
    },
    {
        "id": "darkstore-vosstaniya",
        "address": "Санкт-Петербург, площадь Восстания, 2",
        "lat": 59.9311,
        "lon": 30.3609,
    },
    {
        "id": "darkstore-sevkabel",
        "address": "Санкт-Петербург, Кожевенная линия, 40",
        "lat": 59.9292,
        "lon": 30.2416,
    },
]
CATEGORIES = [
    {"id": 1, "title": "Молочные продукты"},
    {"id": 2, "title": "Фрукты и овощи"},
    {"id": 3, "title": "Хлеб и выпечка"},
    {"id": 4, "title": "Мясо и колбасы"},
    {"id": 5, "title": "Сыры"},
    {"id": 6, "title": "Напитки"},
    {"id": 7, "title": "Сладости"},
    {"id": 8, "title": "Бакалея"},
    {"id": 9, "title": "Заморозка"},
    {"id": 10, "title": "Готовая еда"},
]
PRODUCT_GROUPS = [
    (1, "Молоко", ["1.5%", "2.5%", "3.2%", "безлактозное", "топленое"]),
    (1, "Йогурт", ["клубника", "персик", "черника", "натуральный", "греческий"]),
    (1, "Кефир", ["1%", "2.5%", "3.2%", "термостатный", "био"]),
    (2, "Бананы", ["мини", "отборные", "органические", "желтые", "зеленые"]),
    (2, "Яблоки", ["гала", "голден", "гренни смит", "фуджи", "айдаред"]),
    (2, "Томаты", ["черри", "сливка", "розовые", "бакинские", "на ветке"]),
    (3, "Хлеб", ["бородинский", "пшеничный", "ржаной", "зерновой", "тостовый"]),
    (3, "Булочка", ["с маком", "с корицей", "бриошь", "картофельная", "молочная"]),
    (4, "Колбаса", ["докторская", "сервелат", "краковская", "сырокопченая", "молочная"]),
    (4, "Курица", ["филе", "бедро", "голень", "крылья", "фарш"]),
    (5, "Сыр", ["гауда", "чеддер", "пармезан", "моцарелла", "сулугуни"]),
    (5, "Творожный сыр", ["сливочный", "с зеленью", "с грибами", "легкий", "острый"]),
    (6, "Вода", ["газированная", "негазированная", "минеральная", "детская", "лимон"]),
    (6, "Сок", ["яблоко", "апельсин", "томат", "вишня", "мультифрукт"]),
    (7, "Шоколад", ["молочный", "темный", "с орехом", "с карамелью", "горький"]),
    (7, "Конфеты", ["трюфель", "пралине", "желейные", "вафельные", "карамель"]),
    (8, "Макароны", ["спагетти", "перья", "рожки", "фузилли", "лингвини"]),
    (8, "Рис", ["басмати", "жасмин", "круглый", "бурый", "для плова"]),
    (9, "Пельмени", ["сибирские", "домашние", "говядина", "индейка", "мини"]),
    (9, "Мороженое", ["ваниль", "шоколад", "фисташка", "пломбир", "эскимо"]),
    (10, "Салат", ["оливье", "цезарь", "греческий", "крабовый", "витаминный"]),
    (10, "Сэндвич", ["курица", "ветчина", "тунец", "сыр", "индейка"]),
]
PACKAGES = ["200 г", "300 г", "450 г", "500 г", "750 г", "1 кг"]
BRANDS = ["Ладога", "Север", "Ферма 78", "Петербургский", "Балтийский"]


class ReservationRequest(BaseModel):
    sku_id: str
    quantity: int


class ReservationsRequest(BaseModel):
    items: list[ReservationRequest]


async def _simulate_latency() -> None:
    await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
    if random.random() < SLOW_RESPONSE_PROBABILITY:
        await asyncio.sleep(
            random.uniform(MIN_SLOW_DELAY_SECONDS, MAX_SLOW_DELAY_SECONDS),
        )


def _check_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный API-ключ",
        )


def _generate_products() -> list[dict[str, str | int | bool]]:
    products = []
    sku_number = 1

    for category_id, base_title, variants in PRODUCT_GROUPS:
        category_title = CATEGORIES[category_id - 1]["title"]
        for variant in variants:
            for package in PACKAGES:
                for brand in BRANDS:
                    products.append(
                        {
                            "sku_id": f"sku-{sku_number}",
                            "title": f"{base_title} {variant} {brand} {package}",
                            "description": f"{base_title} {variant}, упаковка {package}",
                            "category_id": category_id,
                            "category_title": category_title,
                            "price": 80 + category_id * 20 + sku_number % 170,
                            "is_active": True,
                        }
                    )
                    sku_number += 1

    return products


PRODUCTS = _generate_products()


def _shuffle_key(product: dict[str, str | int | bool]) -> str:
    return hashlib.sha256(str(product["sku_id"]).encode()).hexdigest()


def _get_shuffled_products(
    products: list[dict[str, str | int | bool]],
) -> list[dict[str, str | int | bool]]:
    return sorted(products, key=_shuffle_key)


def _get_darkstore_index(darkstore_id: str) -> int:
    for index, darkstore in enumerate(DARKSTORES):
        if darkstore["id"] == darkstore_id:
            return index

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Даркстор не найден",
    )


def _get_available_products(darkstore_id: str) -> list[dict[str, str | int | bool]]:
    darkstore_index = _get_darkstore_index(darkstore_id)
    available_products = []

    for index, product in enumerate(PRODUCTS):
        availability_key = f"{product['sku_id']}:{darkstore_id}"
        availability_score = int(
            hashlib.sha256(availability_key.encode()).hexdigest(),
            16,
        )
        is_available_in_darkstore = (
            availability_score % 100 < DARKSTORE_ASSORTMENT_PERCENT
        )

        if not is_available_in_darkstore:
            continue

        available_products.append(
            {
                **product,
                "quantity": 15 + (index + darkstore_index) % 80,
                "is_available": True,
            }
        )

    return available_products


@app.get("/darkstores")
async def get_darkstores(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> list[dict[str, str | float]]:
    _check_api_key(x_api_key)
    await _simulate_latency()
    return DARKSTORES


@app.get("/products")
async def get_products(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> list[dict[str, str | int | bool]]:
    _check_api_key(x_api_key)
    await _simulate_latency()
    return _get_shuffled_products(PRODUCTS)


@app.get("/darkstores/items")
async def get_all_darkstore_items(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, dict[str, list[dict[str, str | int | bool]]]]:
    _check_api_key(x_api_key)
    await _simulate_latency()

    return {
        "items_by_darkstore": {
            str(darkstore["id"]): _get_shuffled_products(
                _get_available_products(str(darkstore["id"])),
            )
            for darkstore in DARKSTORES
        },
    }


@app.get("/darkstore/suitable")
async def get_suitable_darkstore(
    lat: float,
    lon: float,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    _check_api_key(x_api_key)
    await _simulate_latency()

    darkstore = min(
        DARKSTORES,
        key=lambda item: (item["lat"] - lat) ** 2 + (item["lon"] - lon) ** 2,
    )
    return darkstore["id"]


@app.post("/reservations")
async def reserve_items(
    data: ReservationsRequest,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, str]:
    _check_api_key(x_api_key)
    await _simulate_latency()

    for item in data.items:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Количество должно быть положительным",
            )

    return {
        "reservation_id": f"res-{secrets.token_hex(8)}",
    }
