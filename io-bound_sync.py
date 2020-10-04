# io-bound_sync.py

import time

from tasks import make_request


def main():
    for num in range(1, 101):
        make_request(num)


if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
