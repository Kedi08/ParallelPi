import argparse
import threading
import multiprocessing
import queue
import time
import math
import os
import subprocess
import sys


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

def run_local_segment(start: int, end: int):
    """Compute a single segment and print only the partial result."""
    partial = 4 * compute_segment(start, end)
    print(f"π ≈ {partial}")
    return


def distribute_across_hosts(iterations: int, hosts: list):
    """
    Split the range [0, iterations) into len(hosts) segments,
    SSH to each host to compute its chunk, collect and sum the partial results.
    """
    n_hosts = len(hosts)
    chunk = iterations // n_hosts
    host_segments = []
    for idx, host in enumerate(hosts):
        start = idx * chunk
        end = start + chunk if idx < n_hosts - 1 else iterations
        host_segments.append((host, start, end))

    total = 0.0
    for host, start, end in host_segments:
        # Build the SSH command. Assumes that 'pi.py' is available in PATH or in the
        # same directory on the remote host, and that 'python3' is installed.
        # We pass --start and --end to make the remote compute only that segment.
        cmd = [
            "ssh",
            host,
            "python3",
            "pi.py",
            "--start",
            str(start),
            "--end",
            str(end),
        ]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error on host {host}: {e.stderr.strip()}", file=sys.stderr)
            sys.exit(1)

        # Parse the first line: "π ≈ {partial_value}"
        first_line = output.strip().splitlines()[0]
        try:
            partial_val = float(first_line.split("≈")[1].strip())
        except Exception as e:
            print(f"Failed to parse output from host {host}: '{first_line}'", file=sys.stderr)
            sys.exit(1)

        total += partial_val

    return total

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
    parser.add_argument('--hosts', type=str, help="comma-separated list of hosts for distributed computation")
    parser.add_argument('--start', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--end', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()

    start_time = time.time()
     # If --start and --end are provided, this instance is acting as a worker for a single segment.
    if args.start is not None and args.end is not None:
        run_local_segment(args.start, args.end)
        return

    # Distributed mode across multiple hosts
    elif args.hosts:
        if not args.iterations:
            parser.error("When using --hosts, you must also specify -i / --iterations.")
        hosts = args.hosts.split(',')
        start_time = time.time()
        result = distribute_across_hosts(args.iterations, hosts)
        elapsed = time.time() - start_time
        error = abs(math.pi - result)
        print(f"π ≈ {result}")
        print(f"Error = {error}")
        print(f"Time elapsed: {elapsed:.4f}s")
        return
    elif args.with_gil:
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
