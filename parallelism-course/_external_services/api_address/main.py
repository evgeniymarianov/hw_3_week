import asyncio
import hashlib
import json
import math
import random
import secrets
import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


app = FastAPI(title="API Адресов")
bearer_scheme = HTTPBearer(auto_error=False)

CLIENT_ID = "addrs-clid-A9f3K7mQ2xP8rT5n"
CLIENT_SECRET = "addrs-scrt-s8D4qW7zL2pV9cH6bN3y"
TOKENS_DB_PATH = "tokens.json"
ACCESS_TOKEN_TTL_SECONDS = 30
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
MIN_DELAY_SECONDS = 0.1
MAX_DELAY_SECONDS = 0.2
SLOW_RESPONSE_PROBABILITY = 0.1
MIN_SLOW_DELAY_SECONDS = 1.0
MAX_SLOW_DELAY_SECONDS = 2.0
request_counts_by_ip: dict[str, tuple[int, int]] = {}
ADDRESSES = [
    {
        "id": "addr-1",
        "address_text": "Санкт-Петербург, Миллионная улица, 23",
        "lat": 59.9410,
        "lon": 30.3210,
    },
    {
        "id": "addr-2",
        "address_text": "Санкт-Петербург, Малая Морская улица, 5",
        "lat": 59.9366,
        "lon": 30.3148,
    },
    {
        "id": "addr-3",
        "address_text": "Санкт-Петербург, улица Рубинштейна, 15",
        "lat": 59.9296,
        "lon": 30.3449,
    },
    {
        "id": "addr-4",
        "address_text": "Санкт-Петербург, 6-я линия Васильевского острова, 43",
        "lat": 59.9408,
        "lon": 30.2786,
    },
    {
        "id": "addr-5",
        "address_text": "Санкт-Петербург, Каменноостровский проспект, 35",
        "lat": 59.9664,
        "lon": 30.3112,
    },
    {
        "id": "addr-6",
        "address_text": "Санкт-Петербург, Московский проспект, 183-185",
        "lat": 59.8523,
        "lon": 30.3217,
    },
    {
        "id": "addr-7",
        "address_text": "Санкт-Петербург, Ленинский проспект, 129",
        "lat": 59.8518,
        "lon": 30.2520,
    },
    {
        "id": "addr-8",
        "address_text": "Санкт-Петербург, проспект Большевиков, 9",
        "lat": 59.9073,
        "lon": 30.4838,
    },
    {
        "id": "addr-9",
        "address_text": "Санкт-Петербург, Комендантский проспект, 58",
        "lat": 60.0197,
        "lon": 30.2384,
    },
    {
        "id": "addr-10",
        "address_text": "Санкт-Петербург, улица Савушкина, 141",
        "lat": 59.9867,
        "lon": 30.2119,
    },
    {
        "id": "addr-11",
        "address_text": "Санкт-Петербург, улица Розовых Штанов, 4",
        "lat": 59.9315,
        "lon": 30.3601,
    },
    {
        "id": "addr-12",
        "address_text": "Санкт-Петербург, улица Розовых Штанов, 11",
        "lat": 59.9321,
        "lon": 30.3610,
    },
    {
        "id": "addr-13",
        "address_text": "Санкт-Петербург, улица Розовых Штанов, 19",
        "lat": 59.9308,
        "lon": 30.3594,
    },
    {
        "id": "addr-14",
        "address_text": "Санкт-Петербург, улица Розовых Штанов, 27",
        "lat": 59.9319,
        "lon": 30.3586,
    },
    {
        "id": "addr-15",
        "address_text": "Санкт-Петербург, проспект Синих Штанов, 3",
        "lat": 59.9542,
        "lon": 30.3068,
    },
    {
        "id": "addr-16",
        "address_text": "Санкт-Петербург, проспект Синих Штанов, 8",
        "lat": 59.9535,
        "lon": 30.3074,
    },
    {
        "id": "addr-17",
        "address_text": "Санкт-Петербург, проспект Синих Штанов, 16",
        "lat": 59.9549,
        "lon": 30.3059,
    },
    {
        "id": "addr-18",
        "address_text": "Санкт-Петербург, проспект Синих Штанов, 24",
        "lat": 59.9553,
        "lon": 30.3081,
    },
    {
        "id": "addr-19",
        "address_text": "Санкт-Петербург, проспект Синих Штанов, 35",
        "lat": 59.9538,
        "lon": 30.3047,
    },
    {
        "id": "addr-20",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 2",
        "lat": 59.9218,
        "lon": 30.3385,
    },
    {
        "id": "addr-21",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 6",
        "lat": 59.9224,
        "lon": 30.3392,
    },
    {
        "id": "addr-22",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 13",
        "lat": 59.9211,
        "lon": 30.3378,
    },
    {
        "id": "addr-23",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 21",
        "lat": 59.9220,
        "lon": 30.3369,
    },
    {
        "id": "addr-24",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 34",
        "lat": 59.9207,
        "lon": 30.3398,
    },
    {
        "id": "addr-25",
        "address_text": "Санкт-Петербург, аллея Зеленых Штанов, 42",
        "lat": 59.9228,
        "lon": 30.3381,
    },
]


class TokenRefreshRequest(BaseModel):
    client_id: str
    client_secret: str


def _shuffle_key(address: dict[str, str | float]) -> str:
    return hashlib.sha256(str(address["id"]).encode()).hexdigest()


def _get_shuffled_addresses(
    addresses: list[dict[str, str | float]],
) -> list[dict[str, str | float]]:
    return sorted(addresses, key=_shuffle_key)


@app.middleware("http")
async def limit_requests_by_ip(request: Request, call_next):
    client_ip = request.client.host if request.client is not None else "unknown"
    window_id = _get_current_window_id()
    current_window_id, request_count = request_counts_by_ip.get(client_ip, (window_id, 0))

    if current_window_id != window_id:
        current_window_id = window_id
        request_count = 0

    if request_count >= RATE_LIMIT_REQUESTS:
        return _get_rate_limit_response("Слишком много запросов")

    request_counts_by_ip[client_ip] = (current_window_id, request_count + 1)
    return await call_next(request)


def _get_current_window_id() -> int:
    return int(time.time() // RATE_LIMIT_WINDOW_SECONDS)


def _get_retry_after_seconds() -> int:
    seconds_until_next_window = RATE_LIMIT_WINDOW_SECONDS - (
        time.time() % RATE_LIMIT_WINDOW_SECONDS
    )
    return max(1, math.ceil(seconds_until_next_window))


def _get_rate_limit_response(detail: str) -> JSONResponse:
    retry_after = _get_retry_after_seconds()
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": detail},
        headers={"Retry-After": str(retry_after)},
    )


async def _simulate_latency() -> None:
    await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
    if random.random() < SLOW_RESPONSE_PROBABILITY:
        await asyncio.sleep(
            random.uniform(MIN_SLOW_DELAY_SECONDS, MAX_SLOW_DELAY_SECONDS),
        )


async def _get_forced_response(
    code: int | None,
    delay: int | None,
) -> JSONResponse | None:
    if delay is not None:
        if delay < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="delay должен быть больше или равен 0",
            )
        await asyncio.sleep(delay)

    if code is None:
        return None

    if code < 100 or code > 599:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code должен быть HTTP-статусом от 100 до 599",
        )

    if code == status.HTTP_429_TOO_MANY_REQUESTS:
        return _get_rate_limit_response(f"Имитированный ответ {code}")

    return JSONResponse(
        status_code=code,
        content={"detail": f"Имитированный ответ {code}"},
    )


def _check_authorization(
    credentials: HTTPAuthorizationCredentials | None = None,
) -> None:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не передан заголовок авторизации",
        )

    if (
        credentials.scheme.lower() != "bearer"
        or credentials.credentials not in _get_active_tokens()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный access-токен",
        )


def _get_active_tokens() -> dict[str, float]:
    with open(TOKENS_DB_PATH) as file:
        data = json.load(file)

    now = time.time()
    access_tokens = data["access_tokens"]
    active_tokens = {
        token: expires_at
        for token, expires_at in access_tokens.items()
        if expires_at > now
    }

    if active_tokens != access_tokens:
        _save_tokens(active_tokens)

    return active_tokens


def _save_issued_token(access_token: str) -> None:
    tokens = _get_active_tokens()
    tokens[access_token] = time.time() + ACCESS_TOKEN_TTL_SECONDS

    _save_tokens(tokens)


def _save_tokens(tokens: dict[str, float]) -> None:
    with open(TOKENS_DB_PATH, "w") as file:
        json.dump(
            {"access_tokens": tokens},
            file,
        )


@app.post("/auth/token/refresh", response_model=None)
async def refresh_token(
    data: TokenRefreshRequest,
    code: int | None = None,
    delay: int | None = None,
) -> dict[str, str] | JSONResponse:
    forced_response = await _get_forced_response(code, delay)
    if forced_response is not None:
        return forced_response

    if data.client_id != CLIENT_ID or data.client_secret != CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректные клиентские учетные данные",
        )

    await _simulate_latency()

    access_token = secrets.token_urlsafe(32)
    _save_issued_token(access_token)

    return {"access_token": access_token}


@app.get("/suggest", response_model=None)
async def suggest_addresses(
    query: str,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    code: int | None = None,
    delay: int | None = None,
) -> dict[str, list[dict[str, str | float]]] | JSONResponse:
    forced_response = await _get_forced_response(code, delay)
    if forced_response is not None:
        return forced_response

    _check_authorization(credentials)
    await _simulate_latency()

    normalized_query = query.strip().lower()
    suggestions = [
        address
        for address in ADDRESSES
        if normalized_query in address["address_text"].lower()
    ]

    if not normalized_query:
        suggestions = ADDRESSES

    return {
        "suggestions": _get_shuffled_addresses(suggestions),
    }


@app.get("/resolve", response_model=None)
async def resolve_address(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    address_id: str | None = None,
    address: str | None = None,
    code: int | None = None,
    delay: int | None = None,
) -> dict[str, str | float] | JSONResponse:
    forced_response = await _get_forced_response(code, delay)
    if forced_response is not None:
        return forced_response

    _check_authorization(credentials)
    await _simulate_latency()

    if address_id is None and address is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нужно передать address_id или address",
        )

    if address_id is not None:
        for address_item in ADDRESSES:
            if address_item["id"] == address_id:
                return {
                    "address_text": address_item["address_text"],
                    "lat": address_item["lat"],
                    "lon": address_item["lon"],
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Адрес не найден",
        )

    return {
        "address_text": address,
        "lat": 59.9386,
        "lon": 30.3141,
    }
