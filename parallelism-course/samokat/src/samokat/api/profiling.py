import logging
import re
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from samokat.config import ProfilingConfig
from samokat.infrastructure.postgres.query_counter import (
    get_sql_query_stats,
    log_repeated_sql_queries,
    start_sql_query_counting,
    stop_sql_query_counting,
)

logger = logging.getLogger(__name__)


def setup_profiling_middleware(
    app: FastAPI,
    config: ProfilingConfig,
) -> None:
    if not config.enabled:
        return

    pyinstrument_profiler_class = _get_pyinstrument_profiler_class(config)

    if pyinstrument_profiler_class is not None:
        app.mount(
            config.public_path,
            StaticFiles(directory=_ensure_output_directory(config.output_directory)),
            name="pyinstrument-profiles",
        )

    @app.middleware("http")
    async def profile_request(request: Request, call_next):
        if _is_profile_asset_request(request, config):
            return await call_next(request)

        sql_query_count_token = start_sql_query_counting()
        operation_name = f"{request.method.lower()}-{request.url.path}"
        pyinstrument_profiler = None
        if pyinstrument_profiler_class is not None:
            pyinstrument_profiler = pyinstrument_profiler_class(
                interval=config.interval,
                async_mode="enabled",
            )
            pyinstrument_profiler.start()

        try:
            response = await call_next(request)
        except BaseException:
            if pyinstrument_profiler is not None:
                pyinstrument_profiler.stop()
                save_pyinstrument_profile(
                    operation_name=operation_name,
                    profiler=pyinstrument_profiler,
                    config=config,
                    base_url=str(request.base_url),
                )
            sql_query_stats = get_sql_query_stats()
            if sql_query_stats is not None:
                log_repeated_sql_queries(
                    method=request.method,
                    path=request.url.path,
                    stats=sql_query_stats,
                )
            raise
        else:
            if pyinstrument_profiler is not None:
                pyinstrument_profiler.stop()
                profile_urls = save_pyinstrument_profile(
                    operation_name=operation_name,
                    profiler=pyinstrument_profiler,
                    config=config,
                    base_url=str(request.base_url),
                )
                response.headers["X-Profile-Url"] = profile_urls.html_url
                response.headers["X-Profile-Self-Url"] = profile_urls.self_url

            sql_query_stats = get_sql_query_stats()
            if sql_query_stats is not None:
                response.headers["X-SQL-Query-Count"] = str(sql_query_stats.count)
                log_repeated_sql_queries(
                    method=request.method,
                    path=request.url.path,
                    stats=sql_query_stats,
                )
        finally:
            stop_sql_query_counting(sql_query_count_token)

        return response


def _get_pyinstrument_profiler_class(config: ProfilingConfig) -> Any | None:
    if not config.pyinstrument_enabled:
        return None

    try:
        from pyinstrument import Profiler
    except ImportError:
        logger.warning(
            "Pyinstrument profiling is enabled, but pyinstrument is not installed"
        )
        return None

    return Profiler


def _ensure_output_directory(directory: str) -> Path:
    output_directory = Path(directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def _is_profile_asset_request(request: Request, config: ProfilingConfig) -> bool:
    request_path = request.url.path.rstrip("/")
    profile_paths = (config.public_path.rstrip("/"),)
    return any(
        request_path == path or request_path.startswith(f"{path}/")
        for path in profile_paths
    )


def save_pyinstrument_profile(
    operation_name: str,
    profiler: Any,
    config: ProfilingConfig,
    base_url: str | None = None,
) -> "ProfileUrls":
    output_directory = _ensure_output_directory(config.output_directory)

    stem = _build_profile_stem(operation_name)
    html_filename = f"{stem}.html"
    self_filename = f"{stem}-self.txt"

    (output_directory / html_filename).write_text(profiler.output_html())
    (output_directory / self_filename).write_text(
        profiler.output_text(
            unicode=True,
            color=False,
            show_all=True,
            flat=True,
            flat_time="self",
        ),
    )

    return ProfileUrls(
        html_url=_build_profile_location(
            base_url, config.public_path, config.output_directory, html_filename
        ),
        self_url=_build_profile_location(
            base_url, config.public_path, config.output_directory, self_filename
        ),
    )


def _build_profile_location(
    base_url: str | None,
    public_path: str,
    output_directory: str,
    filename: str,
) -> str:
    if base_url is None:
        return str(Path(output_directory) / filename)

    normalized_public_path = public_path.strip("/")
    return str(base_url.rstrip("/") + f"/{normalized_public_path}/{filename}")


def _build_profile_stem(operation_name: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    operation_slug = _slugify_path(operation_name)
    return f"{timestamp}-{operation_slug}"


def _slugify_path(path: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-").lower()
    return slug or "root"


class ProfileUrls:
    def __init__(
        self,
        html_url: str,
        self_url: str,
    ) -> None:
        self.html_url = html_url
        self.self_url = self_url
