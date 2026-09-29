import asyncio


queue = asyncio.Queue()


async def producer():
    for i in range(10):
        await queue.put(i)
        await asyncio.sleep(0.5)


async def consumer():
    events = []
    while True:
        try:
            new_event = await asyncio.wait_for(queue.get(), timeout=5)
            print(new_event)
            events.append(new_event)
        except asyncio.TimeoutError:
            if events:
                print("по истечение 5 секунд отправляем данные", events)
            events = []


async def main():
    await asyncio.gather(
        producer(),
        consumer(),
    )

if __name__ == '__main__':
    asyncio.run(main())
