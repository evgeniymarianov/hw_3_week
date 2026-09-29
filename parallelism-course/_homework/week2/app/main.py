from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.add_event_data import add_event_data_to_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await add_event_data_to_db()
    yield


app = FastAPI(title="API Афиши", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
