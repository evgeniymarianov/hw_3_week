# thread-safe
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class Stock:
    def __init__(self):
        self.quantity = 100
        self._lock = Lock()

    def reserve_stock(self, quantity: int):
        with self._lock:
            curr_quantity = self.quantity
            time.sleep(0.001)
            self.quantity = curr_quantity - quantity


def not_threadsafe():
    stock = Stock()
    with ThreadPoolExecutor(max_workers=10) as executor:
        for _ in range(10):
            executor.submit(stock.reserve_stock, 10)
    print("Осталось", stock.quantity)


if __name__ == '__main__':
    not_threadsafe()
