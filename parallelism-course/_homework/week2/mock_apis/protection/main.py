import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Mock Ticket Protection API")
protection_counter = 0
success_counter = 0
protection_counter_lock = asyncio.Lock()


class ProtectionCalculation(BaseModel):
    booking_id: int
    ticket_amount: int = Field(gt=0)
    event_category: str
    event_starts_at: datetime


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/protection/calculate")
async def calculate(payload: ProtectionCalculation) -> dict:
    global protection_counter
    global success_counter

    async with protection_counter_lock:
        protection_counter += 1
        request_number = protection_counter
        if request_number % 4 == 0 or request_number % 3 == 0:
            success_number = None
        else:
            success_counter += 1
            success_number = success_counter

    if request_number % 4 == 0:
        await asyncio.sleep(7)
        raise HTTPException(status_code=500, detail="Protection service internal error")
    if request_number % 3 == 0:
        await asyncio.sleep(10)
        raise HTTPException(status_code=503, detail="Protection service unavailable")

    await asyncio.sleep(1.5 if success_number % 2 else 4)

    unavailable_categories = {"free", "charity"}
    available = payload.event_category.lower() not in unavailable_categories
    price = max(round(payload.ticket_amount * 0.07), 50) if available else 0
    return {
        "available": available,
        "price": price,
        "covered_amount": payload.ticket_amount if available else 0,
        "description": "Возврат стоимости билетов при страховом случае" if available else None,
    }
