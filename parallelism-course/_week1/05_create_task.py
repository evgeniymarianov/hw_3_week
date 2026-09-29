import asyncio
import time

import httpx


async def get_user(user_id: int):
    print("start user")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/users/{user_id}?delay=200")
    print("end user")
    return resp.json()


async def get_post(post_id: int):
    print("start post")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/posts/{post_id}?delay=500")
    print("end post")
    return resp.json()


async def get_data():
    start = time.perf_counter()
    # await get_user(1)
    # await get_post(23)

    coro_user = get_user(1)
    coro_post = get_post(23)

    task_user: asyncio.Task = asyncio.create_task(coro_user)
    task_post: asyncio.Task = asyncio.create_task(coro_post)

    await asyncio.sleep(0.1)
    task_user.cancel()

    result_post = await task_post
    result_user = await task_user
    end = time.perf_counter()
    print(end-start)


if __name__ == '__main__':
    asyncio.run(get_data())
