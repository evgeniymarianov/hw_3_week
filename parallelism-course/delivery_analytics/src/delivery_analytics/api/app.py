from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from delivery_analytics.api.exceptions import setup_exception_handlers
from delivery_analytics.api.lifespan import create_lifespan
from delivery_analytics.api.routes import main_router


def create_app(container: AsyncContainer) -> FastAPI:
    app = FastAPI(title="Аналитика перемещения курьеров", lifespan=create_lifespan(container))
    setup_dishka(container=container, app=app)
    setup_exception_handlers(app)
    app.include_router(main_router)
    return app
