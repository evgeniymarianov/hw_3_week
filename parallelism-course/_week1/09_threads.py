import threading
import time
from concurrent.futures import ThreadPoolExecutor

from dataclasses import dataclass


@dataclass(slots=True)
class UserStats:
    user_id: int
    score: int
    is_active: bool


COUNT = 5_000_000


def build_user_stats():
    total_score = 0

    for i in range(COUNT):
        user_stat = UserStats(
            user_id=i,
            score=i % 100,
            is_active=i % 2 == 0,
        )
        total_score += user_stat.score ** 2

    return total_score


def sequential():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    build_user_stats()
    build_user_stats()
    build_user_stats()
    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"CPU: {end_cpu-start_cpu}")
    print(f"WALL: {end_wall-start_wall}")


def threads_func():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    threads = [threading.Thread(target=build_user_stats) for _ in range(3)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"CPU: {end_cpu-start_cpu}")
    print(f"WALL: {end_wall-start_wall}")


def threads_pool():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(build_user_stats)
        executor.submit(build_user_stats)
        executor.submit(build_user_stats)

    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"CPU: {end_cpu-start_cpu}")
    print(f"WALL: {end_wall-start_wall}")


if __name__ == '__main__':
    sequential()
    threads_func()
    threads_pool()
