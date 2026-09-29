import asyncio

import httpx


async def get_user(user_id: int):
    print("start user")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/users/{user_id}?delay=2000")
    print("end user")
    return resp.json()


async def get_post(post_id: int):
    print("start post")
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/posts/{post_id}?delay=500")
    print("end post")
    return resp.json()


async def get_data_1():
    try:
        result = await asyncio.wait_for(get_user(1), timeout=3)
        print(f"{result=}")
    except asyncio.TimeoutError as ex:
        print(type(ex))


async def get_llm_data():
    print("start generating")
    await asyncio.sleep(10)
    print("end generating")
    return "IMAGE"


async def get_data_2():
    try:
        async with asyncio.timeout(3):
            result = await asyncio.gather(
                get_user(1),
                get_post(23),
            )
            print(f"{result=}")
    except asyncio.TimeoutError as ex:
        print("Ошибка", type(ex))


async def get_data_3():
    task = asyncio.create_task(get_llm_data())
    try:
        async with asyncio.timeout(3):
            await asyncio.shield(task)
    except asyncio.TimeoutError as ex:
        print("Картинка генерируется дольше обычного")

    result = await task
    print(f"{result=}")


if __name__ == '__main__':
    asyncio.run(get_data_1())
    # asyncio.run(get_data_2())
    # asyncio.run(get_data_3())
