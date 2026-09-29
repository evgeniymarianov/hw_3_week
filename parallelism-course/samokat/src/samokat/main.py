import logging

import uvicorn

from samokat.api.app import create_fastapi_app
from samokat.config import Settings
from samokat.ioc import create_container
from samokat.logging_config import configure_logging

logger = logging.getLogger(__name__)


settings = Settings()
configure_logging()
logger.info(
    "Samokat app configured: host=%s port=%s reload=%s",
    settings.app.host,
    settings.app.port,
    settings.app.reload,
)
container = create_container(settings)
app = create_fastapi_app(settings, container)


if __name__ == "__main__":
    uvicorn.run(
        "samokat.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
        loop="uvloop",
    )
