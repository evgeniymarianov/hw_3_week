from dishka import AsyncContainer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dishka.integrations.fastapi import setup_dishka

from samokat.api.exceptions import setup_exception_handlers
from samokat.api.lifespan import create_lifespan
from samokat.api.profiling import setup_profiling_middleware
from samokat.api.routes import main_router
from samokat.config import Settings


def create_fastapi_app(
    settings: Settings,
    container: AsyncContainer,
) -> FastAPI:
    app = FastAPI(
        title="API доставки",
        lifespan=create_lifespan(container),
        debug=False,
        swagger_ui_parameters={
            "displayRequestDuration": True,
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # setup_profiling_middleware(app, settings.profiling)

    setup_dishka(
        container=container,
        app=app,
    )

    setup_exception_handlers(app)

    app.include_router(main_router)
    return app
