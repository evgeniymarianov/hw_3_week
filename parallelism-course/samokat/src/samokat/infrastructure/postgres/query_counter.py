import hashlib
import logging
import re
import sys
from collections import Counter
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from types import FrameType
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger("samokat.sql")

DEFAULT_FUNCTION_QUERY_WARNING_THRESHOLD = 3
DEFAULT_REPEATED_STATEMENT_WARNING_THRESHOLD = 2
SQL_EXAMPLE_LENGTH = 240


@dataclass
class SqlQueryStats:
    count: int = 0
    fingerprints: Counter[str] = field(default_factory=Counter)
    fingerprint_examples: dict[str, str] = field(default_factory=dict)
    functions: Counter[str] = field(default_factory=Counter)
    fingerprint_functions: dict[str, Counter[str]] = field(default_factory=dict)


_global_sql_query_stats = SqlQueryStats()
_logged_function_counts: Counter[str] = Counter()
_logged_fingerprint_counts: Counter[str] = Counter()
_current_sql_query_stats: ContextVar[SqlQueryStats | None] = ContextVar(
    "current_sql_query_stats",
    default=None,
)


def register_sql_query_counter(engine: AsyncEngine) -> None:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def count_sql(conn, cursor, statement, parameters, context, executemany):
        normalized_statement = _normalize_statement(statement)
        fingerprint = _fingerprint_statement(normalized_statement, context)
        project_call_stack = _get_project_call_stack()

        _record_sql_query(
            stats=_global_sql_query_stats,
            fingerprint=fingerprint,
            statement=normalized_statement,
            project_call_stack=project_call_stack,
        )
        _log_global_sql_hotspots()

        request_stats = _current_sql_query_stats.get()
        if request_stats is not None:
            _record_sql_query(
                stats=request_stats,
                fingerprint=fingerprint,
                statement=normalized_statement,
                project_call_stack=project_call_stack,
            )


def _record_sql_query(
    stats: SqlQueryStats,
    fingerprint: str,
    statement: str,
    project_call_stack: list[str],
) -> None:
    stats.count += 1
    stats.fingerprints[fingerprint] += 1
    stats.fingerprint_examples.setdefault(fingerprint, statement)
    for function_name in project_call_stack:
        stats.functions[function_name] += 1
        stats.fingerprint_functions.setdefault(fingerprint, Counter())[
            function_name
        ] += 1


def _log_global_sql_hotspots() -> None:
    for fingerprint, count in _global_sql_query_stats.fingerprints.items():
        if count < DEFAULT_REPEATED_STATEMENT_WARNING_THRESHOLD:
            continue

        already_logged_count = _logged_fingerprint_counts[fingerprint]
        if already_logged_count and count < already_logged_count * 2:
            continue

        _logged_fingerprint_counts[fingerprint] = count
        logger.warning(
            "Repeated SQL fingerprint globally: count=%s sql=%s call_sites=%s",
            count,
            _global_sql_query_stats.fingerprint_examples[fingerprint][
                :SQL_EXAMPLE_LENGTH
            ],
            format_top_sql_functions(
                _global_sql_query_stats.fingerprint_functions.get(fingerprint, {}),
                limit=5,
            ),
        )

    for function_name, count in _global_sql_query_stats.functions.items():
        if count < DEFAULT_FUNCTION_QUERY_WARNING_THRESHOLD:
            continue

        already_logged_count = _logged_function_counts[function_name]
        if already_logged_count and count < already_logged_count * 2:
            continue

        _logged_function_counts[function_name] = count
        logger.warning(
            "SQL hotspot: %s executed %s SQL queries so far; top functions: %s; top SQL: %s",
            function_name,
            count,
            format_top_sql_functions(_global_sql_query_stats.functions),
            format_top_sql_fingerprints(_global_sql_query_stats),
        )


def start_sql_query_counting() -> Token[SqlQueryStats | None]:
    return _current_sql_query_stats.set(SqlQueryStats())


def get_sql_query_stats() -> SqlQueryStats | None:
    return _current_sql_query_stats.get()


def log_repeated_sql_queries(
    method: str,
    path: str,
    stats: SqlQueryStats,
    threshold: int = DEFAULT_REPEATED_STATEMENT_WARNING_THRESHOLD,
) -> None:
    repeated_fingerprints = {
        fingerprint: count
        for fingerprint, count in stats.fingerprints.items()
        if count >= threshold
    }
    if not repeated_fingerprints:
        return

    logger.warning(
        "Repeated SQL queries in request: method=%s path=%s total=%s repeated=%s",
        method,
        path,
        stats.count,
        format_top_sql_fingerprints(stats, repeated_fingerprints),
    )

    for fingerprint, count in sorted(
        repeated_fingerprints.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]:
        logger.warning(
            "Repeated SQL statement: method=%s path=%s count=%s sql=%s call_sites=%s",
            method,
            path,
            count,
            stats.fingerprint_examples[fingerprint][:SQL_EXAMPLE_LENGTH],
            format_top_sql_functions(
                stats.fingerprint_functions.get(fingerprint, {}), limit=5
            ),
        )


def stop_sql_query_counting(token: Token[SqlQueryStats | None]) -> None:
    _current_sql_query_stats.reset(token)


def format_top_sql_fingerprints(
    stats: SqlQueryStats,
    fingerprints: dict[str, int] | None = None,
    limit: int = 5,
) -> str:
    if fingerprints is None:
        fingerprints = stats.fingerprints

    if not fingerprints:
        return "none"

    return " | ".join(
        f"{count}x {stats.fingerprint_examples[fingerprint][:160]}"
        for fingerprint, count in sorted(
            fingerprints.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]
    )


def format_top_sql_functions(
    functions: dict[str, int],
    limit: int = 10,
) -> str:
    if not functions:
        return "none"

    return " | ".join(
        f"{count}x {function_name}"
        for function_name, count in sorted(
            functions.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]
    )


def _normalize_statement(statement: str) -> str:
    return re.sub(r"\s+", " ", statement).strip()


def _fingerprint_statement(statement: str, context: Any) -> str:
    cache_key = _get_compiled_cache_key(context)
    if cache_key is not None:
        digest = hashlib.sha256(repr(cache_key).encode()).hexdigest()[:16]
        return f"sqlalchemy:{digest}"

    return f"sql:{_normalize_inlined_literals(statement)}"


def _get_compiled_cache_key(context: Any) -> Any | None:
    compiled = getattr(context, "compiled", None)
    if compiled is None:
        return None

    cache_key = getattr(compiled, "cache_key", None)
    if cache_key is None:
        return None

    return getattr(cache_key, "key", cache_key)


def _normalize_inlined_literals(statement: str) -> str:
    statement = re.sub(r"'(?:''|[^'])*'", "?", statement)
    statement = re.sub(r"\b\d+(?:\.\d+)?\b", "?", statement)
    return statement


def _get_project_call_stack() -> list[str]:
    frame = sys._getframe()
    function_names = []
    seen = set()

    while frame is not None:
        frame_name = _format_project_frame(frame)
        if frame_name is not None and frame_name not in seen:
            function_names.append(frame_name)
            seen.add(frame_name)

        frame = frame.f_back

    return function_names


def _format_project_frame(frame: FrameType) -> str | None:
    filename = frame.f_code.co_filename.replace("\\", "/")
    marker = "/src/samokat/"
    if marker not in filename:
        return None

    if filename.endswith("/infrastructure/postgres/query_counter.py"):
        return None

    relative_filename = "samokat/" + filename.split(marker, 1)[1]
    function_name = _get_qualified_function_name(frame)
    return f"{relative_filename}:{frame.f_lineno} {function_name}"


def _get_qualified_function_name(frame: FrameType) -> str:
    if "self" in frame.f_locals:
        return f"{type(frame.f_locals['self']).__name__}.{frame.f_code.co_name}"

    if "cls" in frame.f_locals:
        return f"{frame.f_locals['cls'].__name__}.{frame.f_code.co_name}"

    return frame.f_code.co_name
