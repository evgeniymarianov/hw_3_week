import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="API платежей")
PAYMENT_DELAY = 0.2
calculation_counter = 0
payment_counter = 0
calculation_counter_lock = asyncio.Lock()
payment_counter_lock = asyncio.Lock()


class PaymentCalculation(BaseModel):
    booking_id: int
    amount: int = Field(gt=0)
    currency: str


class PaymentRequest(PaymentCalculation):
    payment_method: str


async def simulate_network() -> None:
    await asyncio.sleep(PAYMENT_DELAY)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/payment/calculate")
async def calculate(payload: PaymentCalculation) -> dict:
    global calculation_counter

    await simulate_network()
    async with calculation_counter_lock:
        calculation_counter += 1
        request_number = calculation_counter

    if request_number % 6 == 0:
        raise HTTPException(status_code=429, detail="Слишком много запросов на расчет платежа")

    commission = max(round(payload.amount * 0.03), 30)
    return {
        "commission": commission,
        "total": payload.amount + commission,
        "payment_methods": ["bank_card", "sbp"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }


@app.post("/payment/pay")
async def pay(payload: PaymentRequest) -> dict:
    global payment_counter

    await asyncio.sleep(PAYMENT_DELAY)
    if payload.payment_method not in {"bank_card", "sbp"}:
        raise HTTPException(status_code=422, detail="Неподдерживаемый способ оплаты")

    async with payment_counter_lock:
        payment_counter += 1
        request_number = payment_counter

    if request_number % 5 == 0:
        raise HTTPException(status_code=429, detail="Слишком много запросов на оплату")

    return {
        "status": "paid",
        "transaction_id": str(uuid.uuid4()),
        "charged_amount": payload.amount,
        "currency": payload.currency,
    }
