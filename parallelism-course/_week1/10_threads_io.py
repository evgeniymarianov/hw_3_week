from concurrent.futures import ThreadPoolExecutor
import time
import httpx


def get_user(user_id: int):
    return httpx.get(f"https://dummyjson.com/users/{user_id}").json()


def sequential():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    for i in range(5):
        get_user(i)

    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"CPU: {end_cpu-start_cpu}")
    print(f"WALL: {end_wall-start_wall}")


def thread_request():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in range(5):
            executor.submit(get_user, i)

    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"CPU: {end_cpu-start_cpu}")
    print(f"WALL: {end_wall-start_wall}")


if __name__ == '__main__':
    sequential()
    thread_request()