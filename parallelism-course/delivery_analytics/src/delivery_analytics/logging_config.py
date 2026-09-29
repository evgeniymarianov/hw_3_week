import logging

LOG_LEVEL = logging.INFO


def configure_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
