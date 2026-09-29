import asyncio
import time

import httpx


async def get_user(user_id: int | str):
    print("start user")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/users/{user_id}?delay=200")
    resp.raise_for_status()
    print("end user")
    return resp.json()


async def get_post(post_id: int):
    print("start post")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/posts/{post_id}?delay=500")
    print("end post")
    return resp.json()


async def get_notifications_from_db():
    await asyncio.sleep(1)
    raise ValueError


async def get_data_tg():
    start = time.perf_counter()

    try:
        async with asyncio.TaskGroup() as tg:
            task_user: asyncio.Task = tg.create_task(get_user("Artem"))
            task_post: asyncio.Task = tg.create_task(get_post(23))
            task_notif: asyncio.Task = tg.create_task(get_notifications_from_db())
        print(task_user.result())
        print(task_post.result())
        print(task_notif.result())
    except* httpx.HTTPStatusError as exc_group:
        print("1", exc_group)
        for exc in exc_group.exceptions:
            print(f"{exc=}")
    except* ValueError as exc_group:
        print("2", exc_group)

    end = time.perf_counter()
    print(end-start)
    await asyncio.sleep(5)


async def get_data_gather():
    start = time.perf_counter()

    try:
        results = await asyncio.gather(
            get_user("Artem"),
            get_post(23),
            get_notifications_from_db(),
            return_exceptions=True,
        )
        print(f"{results=}")
    except Exception as exc:
        print(exc, type(exc))
    end = time.perf_counter()
    print(end-start)
    await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(get_data_tg())
