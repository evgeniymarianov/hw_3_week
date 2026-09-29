import asyncio
import functools
import logging
import re
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, ParamSpec, TypeVar
from weakref import WeakKeyDictionary

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
_line_profile_task_timings: ContextVar[list[tuple[str, float]] | None] = ContextVar(
    "line_profile_task_timings",
    default=None,
)
_previous_task_factories: WeakKeyDictionary[
    asyncio.AbstractEventLoop,
    Callable[..., asyncio.Task[Any]] | None,
] = WeakKeyDictionary()


def line_profile_async(
    output_directory: str = "profiles/line-profiler",
    enabled: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        if not enabled:
            return func

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            profiler_class = _get_line_profiler_class()
            if profiler_class is None:
                return await func(*args, **kwargs)

            profiler = profiler_class()
            task_timings: list[tuple[str, float]] = []
            _ensure_task_factory_installed(asyncio.get_running_loop())
            timings_token = _line_profile_task_timings.set(task_timings)
            profiler.add_function(func)
            profiler.enable_by_count()

            try:
                return await func(*args, **kwargs)
            finally:
                profiler.disable_by_count()
                _line_profile_task_timings.reset(timings_token)
                profile_path = _save_line_profile(
                    func=func,
                    profiler=profiler,
                    output_directory=output_directory,
                    task_timings=task_timings,
                )
                logger.info(
                    "Line profile for %s saved to %s",
                    func.__qualname__,
                    profile_path,
                )

        return wrapper

    return decorator


def _get_line_profiler_class() -> Any | None:
    try:
        from line_profiler import LineProfiler
    except ImportError:
        logger.warning("Line profiling is enabled, but line-profiler is not installed")
        return None

    return LineProfiler


def _save_line_profile(
    func: Callable[..., Any],
    profiler: Any,
    output_directory: str,
    task_timings: list[tuple[str, float]],
) -> Path:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    profile_path = output_path / f"{_build_profile_stem(func)}.txt"
    with profile_path.open("w", encoding="utf-8") as stream:
        stream.write(f"Line profile for {func.__module__}.{func.__qualname__}\n\n")
        profiler.print_stats(stream=stream, output_unit=0.001, stripzeros=True)
        _write_task_timings(stream, task_timings)

    return profile_path


def _ensure_task_factory_installed(loop: asyncio.AbstractEventLoop) -> None:
    if loop in _previous_task_factories:
        return

    previous_factory = loop.get_task_factory()
    _previous_task_factories[loop] = previous_factory
    loop.set_task_factory(
        functools.partial(
            _line_profile_task_factory,
            previous_factory=previous_factory,
        )
    )


def _line_profile_task_factory(
    loop: asyncio.AbstractEventLoop,
    coro: Any,
    *,
    previous_factory: Callable[..., asyncio.Task[Any]] | None,
    **kwargs: Any,
) -> asyncio.Task[Any]:
    task_timings = _line_profile_task_timings.get()
    if task_timings is not None:
        coro = _profile_task_coro(coro, task_timings)

    if previous_factory is None:
        return asyncio.Task(coro, loop=loop, **kwargs)

    return previous_factory(loop, coro, **kwargs)


async def _profile_task_coro(
    coro: Awaitable[R],
    task_timings: list[tuple[str, float]],
) -> R:
    started_at = perf_counter()
    try:
        return await coro
    finally:
        task = asyncio.current_task()
        name = task.get_name() if task is not None else _format_awaitable_name(coro)
        task_timings.append((name, (perf_counter() - started_at) * 1000))


def _write_task_timings(
    stream: Any,
    task_timings: list[tuple[str, float]],
) -> None:
    if not task_timings:
        return

    stream.write("\nAsync tasks wall time (ms):\n")
    for name, elapsed_ms in sorted(
        task_timings,
        key=lambda task_timing: task_timing[1],
        reverse=True,
    ):
        stream.write(f"  {name}: {elapsed_ms:.1f}\n")


def _format_awaitable_name(awaitable: Awaitable[Any]) -> str:
    code = getattr(awaitable, "cr_code", None)
    if code is not None:
        return code.co_qualname

    return type(awaitable).__name__


def _build_profile_stem(func: Callable[..., Any]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    func_slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        f"{func.__module__}.{func.__qualname__}",
    ).strip("-")
    return f"{timestamp}-{func_slug.lower()}"
