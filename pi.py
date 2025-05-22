import argparse
import threading
import multiprocessing
import queue
import subprocess
import time
import math
import functools
import operator
import os


def compute_segment(start: int, end: int) -> float:
    """Compute partial sum of Leibniz series for k in [start, end)."""
    total = 0.0
    for k in range(start, end):
        total += ((-1) ** k) / (2 * k + 1)
    return total


def run_gil_threads(iterations: int, threads: int) -> float:
    """Compute using manual GIL-bound threads."""
    chunk = iterations // threads
    segments = [
        (i * chunk, (i + 1) * chunk if i < threads - 1 else iterations)
        for i in range(threads)
    ]
    results = [0.0] * threads

    def worker(idx: int, seg: tuple):
        results[idx] = compute_segment(*seg)

    ts = []
    for idx, seg in enumerate(segments):
        t = threading.Thread(target=worker, args=(idx, seg))
        t.start()
        ts.append(t)
    for t in ts:
        t.join()
    return 4 * sum(results)


def thread_consumer(tasks: queue.Queue, results: queue.Queue):
    """Consumer thread for producer-consumer pattern."""
    while True:
        seg = tasks.get()
        if seg is None:
            break
        results.put(compute_segment(*seg))


def run_producer_consumer_threads(iterations: int, threads: int) -> float:
    """Compute using producer-consumer architecture with threads."""
    chunk = max(1, iterations // threads)
    segments = [
        (i * chunk, min((i + 1) * chunk, iterations))
        for i in range((iterations + chunk - 1) // chunk)
    ]
    tasks = queue.Queue()
    results = queue.Queue()
    workers = []

    for _ in range(threads):
        t = threading.Thread(target=thread_consumer, args=(tasks, results))
        t.daemon = True
        t.start()
        workers.append(t)

    # Producer enqueues tasks
    for seg in segments:
        tasks.put(seg)
    # Send sentinel to each consumer
    for _ in workers:
        tasks.put(None)

    total = 0.0
    for _ in segments:
        total += results.get()
    return 4 * total


def process_consumer(tasks: multiprocessing.Queue, results: multiprocessing.Queue):
    """Consumer process for producer-consumer pattern."""
    while True:
        seg = tasks.get()
        if seg is None:
            break
        results.put(compute_segment(*seg))


def run_producer_consumer_processes(iterations: int, processes: int) -> float:
    """Compute using producer-consumer architecture with processes."""
    chunk = max(1, iterations // processes)
    segments = [
        (i * chunk, min((i + 1) * chunk, iterations))
        for i in range((iterations + chunk - 1) // chunk)
    ]
    tasks = multiprocessing.Queue()
    results = multiprocessing.Queue()
    workers = []

    for _ in range(processes):
        p = multiprocessing.Process(target=process_consumer, args=(tasks, results))
        p.start()
        workers.append(p)

    for seg in segments:
        tasks.put(seg)
    for _ in workers:
        tasks.put(None)

    total = 0.0
    for _ in segments:
        total += results.get()
    for p in workers:
        p.join()
    return 4 * total


def run_pool(iterations: int, pool_size: int) -> float:
    """Compute using a multiprocessing pool."""
    chunk = max(1, iterations // pool_size)
    segments = [
        (i * chunk, min((i + 1) * chunk, iterations))
        for i in range((iterations + chunk - 1) // chunk)
    ]
    with multiprocessing.Pool(pool_size) as pool:
        results = pool.starmap(compute_segment, segments)
    return 4 * sum(results)


def main():
    parser = argparse.ArgumentParser(description="Parallel PI Calculator")
    parser.add_argument('-i', '--iterations', type=int, help="number of series terms")
    default_threads = os.cpu_count()
    default_cores = default_threads // 2
    parser.add_argument('-t', '--threads', type=int, default=default_threads,
                    help=f"number of threads (default: available threads = {default_threads})")
    parser.add_argument('-p', '--processes', type=int, default=default_cores,
                        help="number of processes (default: approx. physical cores = {default_cores})")
    parser.add_argument('--with-gil', action='store_true', help="use GIL-bound threads")
    parser.add_argument('--with-thread', action='store_true', help="use producer-consumer threads")
    parser.add_argument('--with-process', action='store_true', help="use producer-consumer processes")
    parser.add_argument('--pool', type=int, help="use multiprocessing pool")
    parser.add_argument('-s', '--segments', type=int, help="number of segments for host mode or manual segment mode")
    parser.add_argument('--seg-size', type=int, help="size of each segment")
    args = parser.parse_args()

    start_time = time.time()
    if args.with_gil:
        result = run_gil_threads(args.iterations, args.threads)
    elif args.with_thread:
        result = run_producer_consumer_threads(args.iterations, args.threads)
    elif args.with_process:
        result = run_producer_consumer_processes(args.iterations, args.processes)
    elif args.pool:
        result = run_pool(args.iterations, args.pool)
    elif args.segments and args.seg_size:
        # manual local segments
        total = 0.0
        for i in range(args.segments):
            start = i * args.seg_size
            end = start + args.seg_size
            total += compute_segment(start, end)
        result = 4 * total
    elif args.iterations:
        result = 4 *compute_segment(0, args.iterations)
    else:
        parser.error("No computation mode selected")

    elapsed = time.time() - start_time
    error = abs(math.pi - result)
    print(f"π ≈ {result}")
    print(f"Error = {error}")
    print(f"Time elapsed: {elapsed:.4f}s")


if __name__ == "__main__":
    main()
