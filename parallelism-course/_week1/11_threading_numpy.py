import numpy
import time

from concurrent.futures import ThreadPoolExecutor

import numpy as np


def numpy_sum_of_squares():
    values = np.arange(5_000_000, dtype=np.float64)
    total = 0

    for _ in range(100):
        total += np.sum(values * values)
    return total


def sequential():
    start = time.perf_counter()
    for _ in range(3):
        numpy_sum_of_squares()
    print(time.perf_counter()-start)


def multithreading():
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(numpy_sum_of_squares)
        executor.submit(numpy_sum_of_squares)
        executor.submit(numpy_sum_of_squares)
    print(time.perf_counter()-start)


if __name__ == '__main__':
    sequential()
    multithreading()
