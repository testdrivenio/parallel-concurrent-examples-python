## Parallelism, Concurrency, and AsyncIO in Python - by example

This post looks at how to speed up CPU-bound and IO-bound operations with multiprocessing, threading, and AsyncIO.

## Concurrency vs Parallelism

Concurrency and parallelism are similar terms, but they are not the same thing.

Concurrency is the ability to run multiple tasks on the CPU at the same time. Tasks can start, run, and complete in overlapping time periods. In the case of a single CPU, multiple tasks are run with the help of [context switching](https://en.wikipedia.org/wiki/Context_switch), where the state of a process is stored so that it can be called and executed later.

Parallelism, meanwhile, is the ability to run multiple tasks at the same time across multiple CPU cores.

Though they can increase the speed of your application, concurrency and parallelism should not be used everywhere. The use case depends on whether the task is CPU-bound or IO-bound

Tasks that are limited by the CPU are called CPU-bound task. For example, mathematical computations are CPU-bound, because more CPU means more computation power. IO-bound tasks spend the majority of their time waiting for input/output operations to be completed. For example, interactions with network devices are IO-bound.

Parallelism is for CPU-bound tasks. In theory, If a task is divided into n-subtasks, each of these n-tasks can run in parallel to effectively reduce the time to 1/n of the original non-parallel task. Concurrency is preferred for IO-bound tasks, as you can do something else while the IO resources are being fetched.

The best example of CPU-bound tasks is in data science. Data Scientists deal with huge chunks of data. For data preprocessing, they can split the data into multiple batches and run them in parallel, effectively decreasing the total time to process. Increasing the number of cores results in faster processing.

Web scraping is IO-bound. Because the task has little effect on the CPU since most of the time is spent on reading from and writing to the network. Other common IO-bound tasks include database calls and reading and writing files to disk. Web applications, like Django and Flask, are IO-bound applications.

## Scenario

With that, let's take a look at how to speed up the following tasks:

```python
# tasks.py

import os
from threading import current_thread
from multiprocessing import current_process

import httpx
import requests


def make_request(num):
    # io-bound

    pid = os.getpid()
    thread_name = current_thread().name
    process_name = current_process().name
    print(f"{pid} - {process_name} - {thread_name}")

    requests.get("https://httpbin.org/ip")


async def make_request_async(num, client):
    # io-bound

    pid = os.getpid()
    thread_name = current_thread().name
    process_name = current_process().name
    print(f"{pid} - {process_name} - {thread_name}")

    await client.get("https://httpbin.org/ip")


def get_prime_numbers(num):
    # cpu-bound

    pid = os.getpid()
    thread_name = current_thread().name
    process_name = current_process().name
    print(f"{pid} - {process_name} - {thread_name}")

    numbers = []

    prime = [True for i in range(num + 1)]
    p = 2

    while (p * p <= num):
        if prime[p]:
            for i in range(p * 2, num + 1, p):
                prime[i] = False
        p += 1

    prime[0]= False
    prime[1]= False

    for p in range(num + 1):
        if prime[p]:
            numbers.append(p)

    return numbers
```

We're doing the following tasks

- `make_request` to make http request to the URL, `https://httpbin.org/ip` for the defined `num` times.
- `make_request_async` to make asynchronous http requests, using the `httpx` package.
- `get_prime_numbers ` to calculate all the prime numbers from 2 to the limit provided. The prime numbers are calculated using a method called [Sieve of Erastosthenes](https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes)

We are going to use the following libraries,

- `threading` to create multithreading  tasks
- `multiprocessing` to create multiprocessing tasks
- `concurrent.futures` provides an abstraction to both `threading` and `multiprocessing`. Both these can be implemented from the same library.
- `asyncio` is used to provide concurrency. They work on something called `coroutines` and is managed by the python interpreter. 

| Libraries                      | Methods                                 | Processing Type         |
|--------------------------------|-----------------------------------------|-------------------------|
| threading                      | Thread                                  | concurrent              |
| concurrent.futures             | ThreadPoolExecutor                      | concurrent              |
| asyncio                        | gather                                  | concurrent              |
| multiprocessing                | Pool                                    | parallel                |
| concurrent.futures             | ProcessPoolExecutor                     | parallel                |


## IO-bound Operation

Again, IO-bound tasks spends more time on IO than on the CPU.

Since web scraping is IO bound, we should use threading since the retrieving of the HTML (IO) is slower than parsing it (CPU).

Scenario: How to speed up a Python-based web scraping and crawling script?

## Sync Example

Let's start with a benchmark.

```python
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
```

Here, we make 100 http request using the `make_request` function and the total time elapsed is calculated. Since we are doing it synchronously, each task is executed sequentially. 

Elapsed run time: 14.97437877 seconds.

Roughly 0.15 seconds per task

### Threading Example

```python
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
```

The same `make_request` function is called 100 times, this time we use `threading` library to create a thread for each request. The total time decreases from ~15s to ~1s. `task.start()` will start the task and `task.join()` will wait for it to finish.

Elapsed run time: 1.020112515 seconds.

You might wonder, since we're using separate threads for each request, the whole thing should finish in ~0.15s. This extra time is the overhead for managing threads. The Global Interpreter Lock(GIL) in python makes sure that only one thread is using the python bytecode at a time. Also python uses OS threads. So the OS manages the threads and their call stacks. 

### concurrent.futures Example

```python
# io-bound_concurrent_2.py

import time
from concurrent.futures import ThreadPoolExecutor, wait

from tasks import make_request


def main():
    futures = []

    with ThreadPoolExecutor() as executor:
        for num in range(1, 101):
            futures.append(
                executor.submit(make_request, num)
            )

    wait(futures)


if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
```

Here we used `concurrent.futures.ThreadPoolExecutor` to achieve multithreading. Once we append all the jobs to futures, we wait for it to finish using `wait(futures)`.

Elapsed run time: 1.340592231 seconds

`concurrent.futures.ThreadPoolExecutor` is actually an abstraction around the `multithreading` library which makes it easier to use. In the previous example, we assigned each request to a thread and in total 100 threads were used. But `ThreadPoolExecutor` defaults the number of workers to `min(32, os.cpu_count() + 4)`. ThreadPoolExecutor exists to ease the process of achieving multithreading. If you want more control over multithreading, use `multithreading` library instead. 

### AsyncIO Example

```python
# io-bound_concurrent_3.py

import asyncio
import httpx
import time

from tasks import make_request_async


async def main():
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *[make_request_async(num, client) for num in range(1, 101)]
        )


if __name__ == "__main__":
    start_time = time.perf_counter()

    loop=asyncio.get_event_loop()
    loop.run_until_complete(main())

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed run time: {elapsed_time} seconds")
```

> `httpx` is used here since `requests` does not support async operations.

Here we use `asyncio` to achieve concurrency. 

Elapsed run time: 0.553961068 seconds

TODO: expand on this: why is this faster? if asyncio leverages concurrency, does it do it more efficiently? why is it so much faster? does the event loop have something to do with it?

`asyncio` is faster than other methods, because as said earlier, threading makes use of OS(Operating System) threads. So the threads are managed by the OS, where the thread switching is preempted by the OS. `asyncio` does not use threads, but `coroutines`  which are defined by the python interpreter. With coroutines, the program decides when to switch tasks in an optimal way.  This is handled by the `even_loop` in asyncio. 

## CPU-bound Operation

Scenario: How to speed up a simple data processing script?

### Sync Example

Again, let's start with a benchmark.

```python
# cpu-bound_sync.py

import time

from tasks import get_prime_numbers


def main():
    for num in range(1000, 16000):
        get_prime_numbers(num)


if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
```

Here, we execute the `get_prime_numbers` function for numbers in `[1000, 16000)`

Elapsed run time: 16.180765792 seconds.

### Multiprocessing Example

```python
# cpu-bound_parallel_1.py

import threading
import time
from multiprocessing import Pool, cpu_count

from tasks import get_prime_numbers


def main():
    with Pool(cpu_count() - 1) as p:
        p.starmap(get_prime_numbers, zip(range(1000, 16000)))
        p.close()
        p.join()



if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
```

Here we used multiprocessing to calculate the prime numbers. `Pool.starmap` is the fastest way to map target function to multiple arguments. `Pool.close()` will close the pool and make sure no process joins it. `Pool.join()` will wait for the Pool to finish executing. 

Elapsed run time: 2.9848740599999997 seconds.

### concurrent.futures Example

```python
# cpu-bound_parallel_2.py

import time
from concurrent.futures import ProcessPoolExecutor, wait
from multiprocessing import Pool, cpu_count

from tasks import get_prime_numbers


def main():
    futures = []

    with ProcessPoolExecutor(cpu_count() - 1) as executor:
        for num in range(1000, 16000):
            futures.append(
                executor.submit(get_prime_numbers, num)
            )

    wait(futures)


if __name__ == "__main__":
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    print(f"Elapsed run time: {end_time - start_time} seconds.")
```

Here we achieved multiprocessing using `concurrent.futures.ProcessPoolExecutor`. Once the jobs are added to futures, `wait(futures)` will wait for it to finish. 

Elapsed run time: 4.452427557 seconds.

`concurrent.futures.ProcessPoolExecutor` is a wrapper around `multiprocessing.Pool` . It has the same limitations as the latter. If you want more control over multiprocessing, use `multiprocessing.Pool`. `concurrent.futures` provides an abstraction over both multiprocessing and threading and makes it easy to switch between these two.

## Conclusion

TODO: do you think it's worth adding the parallel examples for the IO-bound task and the concurrent examples for the CPU-bound task to show that they are slower?

Using multiprocessing to execute the `make_request` function will not make it faster than `threaded` one. Because the multiple processes are still waiting for I/O. However the multiprocessing approach will be faster then the sync approach. But threading is recommended for I/O tasks. Also using concurrency for CPU-bound tasks is not worth it when parallelism can give it a great boost.  	

Adding concurrency or parallelism adds complexity, so only use for long running scripts.

concurrent.futures is where I generally start since-

1. It's easy to switch back and forth between concurrency and parallelism
1. The dependent libraries don't need to support asyncio (requests vs httpx)
1. It's clean and easy to read
