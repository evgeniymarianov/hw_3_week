import asyncio
import logging
import random
import time

import httpx

logger = logging.getLogger("samokat.httpx")


async def on_request(request: httpx.Request) -> None:
    request.extensions["started_at"] = time.perf_counter()


async def on_response(response: httpx.Response) -> None:
    started_at = response.request.extensions.get("started_at")
    duration = time.perf_counter() - started_at if started_at is not None else 0

    logger.info(
        "HTTP request completed: method=%s url=%s status=%s duration=%.3fs",
        response.request.method,
        response.request.url,
        response.status_code,
        duration,
    )


class BaseHTTPConnector:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        headers: dict[str, str] | None = None,
        rate_limit_requests: int | None = None,
        rate_limit_interval: int | None = None,
        retry_count: int = 2,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            event_hooks={
                "request": [on_request],
                "response": [on_response],
            },
        )
        self.rate_limit_requests = rate_limit_requests
        if rate_limit_requests:
            self._rate_limiter = asyncio.Semaphore(rate_limit_requests)
            self._rate_limit_interval = rate_limit_interval
        self.retry_count = retry_count

    async def close_client(self):
        await self._client.aclose()

    async def release_rate_limiter_later(self):
        await asyncio.sleep(self._rate_limit_interval + 0.05)
        self._rate_limiter.release()

    async def _exponential_backoff_sleep(self, attempt: int):
        delay = 0.5 * 2 ** (attempt + 1)
        jitter = random.uniform(0.1, 0.5)

        await asyncio.sleep(delay + jitter)

    async def _request(
        self,
        method: str,
        url: str,
        retry: bool = False,
        **kwargs,
    ) -> httpx.Response:
        attempts = self.retry_count if retry else 1

        for attempt in range(attempts):
            if self.rate_limit_requests:
                await self._rate_limiter.acquire()
                _ = asyncio.create_task(  # noqa: RUF006
                    self.release_rate_limiter_later(),
                    name="samokat.http.rate_limiter.release",
                )

            try:
                response = await self._client.request(method, url, **kwargs)
            except (httpx.NetworkError, httpx.TimeoutException):
                if attempt == attempts - 1:
                    raise

                await self._exponential_backoff_sleep(attempt)
                continue

            if (
                response.status_code not in (429, 503) or
                attempt == attempts - 1
            ):
                return response

            await self._exponential_backoff_sleep(attempt)
