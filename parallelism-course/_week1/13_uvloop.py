import asyncio

import uvloop


async def coro():
    await asyncio.sleep(1)


asyncio.run(coro())
uvloop.run(coro())