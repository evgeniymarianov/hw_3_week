import asyncio
import time

import httpx


async def get_user(user_id: int):
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/users/{user_id}?delay=200")
    return resp.json()


async def get_post(post_id: int):
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/posts/{post_id}?delay=500")
    return resp.json()


async def get_data():
    start = time.perf_counter()
    # await get_user(1)
    # await get_post(23)
    result_user, result_post = await asyncio.gather(
        get_user(1),
        get_post(23),
    )
    print(f"{result_user=}")
    print(f"{result_post=}")
    end = time.perf_counter()
    print(end-start)


if __name__ == '__main__':
    asyncio.run(get_data())
