import asyncio

import httpx


async def get_user(user_id: int):
    # TODO: добавить cpu/wall time сравнение
    resp = await httpx.AsyncClient().get(f"https://dummyjson.com/users/{user_id}")
    return resp.json()


async def main():
    obj = get_user(25)
    print(obj, type(obj))

    result = await obj
    print(f"{result=}")


if __name__ == '__main__':
    asyncio.run(main())
