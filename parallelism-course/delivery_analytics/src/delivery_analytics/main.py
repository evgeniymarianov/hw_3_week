import logging

import uvicorn

from delivery_analytics.api.app import create_app
from delivery_analytics.config import Settings
from delivery_analytics.ioc import create_container
from delivery_analytics.logging_config import configure_logging

logger = logging.getLogger(__name__)

settings = Settings()
configure_logging()
container = create_container(settings)
app = create_app(container)


if __name__ == "__main__":
    uvicorn.run(
        "delivery_analytics.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
        loop="uvloop",
    )
