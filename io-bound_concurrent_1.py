# io-bound_concurrent_1.py

import threading
import time

from tasks import make_request


def main():
    tasks = []

    for num in range(1, 101):
        tasks.append(threading.Thread(target=make_request, args=(num,)))
        tasks[-1].start()

    for task in tasks:
        task.join()


if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
