import asyncio
from asyncio import Lock, Semaphore


class FakeSession:
    def __init__(self):
        self.value = 0
        self._lock = Lock()
        self._semaphore = Semaphore(2)

    async def incr_value(self, incr: int):
        async with self._semaphore:
            curr_value = self.value
            await asyncio.sleep(0.00001)
            self.value = curr_value + incr


async def not_coroutine_safe():
    fake_session = FakeSession()
    coros = [fake_session.incr_value(1) for _ in range(10)]
    await asyncio.gather(*coros)
    print("Результат:", fake_session.value)


if __name__ == '__main__':
    asyncio.run(not_coroutine_safe())
