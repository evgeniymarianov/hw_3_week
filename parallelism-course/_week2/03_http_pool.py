import asyncio
import time

import httpx


URL = "https://solvit.space"  # dzen.ru, vk.ru, dummyjson.com
REQUESTS_COUNT = 20


async def measure(title: str, func):
    started_at = time.perf_counter()

    await func()

    seconds = time.perf_counter() - started_at
    print(f"{title}: {seconds:.3f} сек")

    return seconds


async def without_pool():
    for _ in range(REQUESTS_COUNT):
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            print(response.status_code)


async def with_pool():
    async with httpx.AsyncClient() as client:
        for _ in range(REQUESTS_COUNT):
            response = await client.get(URL)
            print(response.status_code)


async def main():
    async with httpx.AsyncClient() as client:
        await client.get(URL)

    await measure("Без пула", without_pool)
    await measure("С пулом ", with_pool)


if __name__ == "__main__":
    asyncio.run(main())
