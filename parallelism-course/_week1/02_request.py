import httpx
import time


url_posts = "https://dummyjson.com/posts?delay=1000"


def get_posts():
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    resp = httpx.get(url_posts)
    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    print(f"{end_wall-start_wall}")
    print(f"{end_cpu-start_cpu}")
    return resp.json()


if __name__ == '__main__':
    get_posts()
