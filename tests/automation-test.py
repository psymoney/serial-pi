# benchmark.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import psutil
import os

# --------- CONFIG ---------
TEST_DURATION_SEC = 60
CAMERA_INTERVAL_SEC = 0.2  # 5 Hz
SERIAL_INTERVAL_SEC = 0.1  # 10 Hz
SERIAL_PORTS = 2
CAMERA_FILENAME_TEMPLATE = "image_{count}.jpg"
# --------------------------

# === MOCK FUNCTIONS (simulate work) ===


def mock_picamera_capture(filename):
    # Simulate 30~50ms capture time (realistic for low-res capture)
    time.sleep(0.04)


def mock_serial_communication(port_name):
    # Simulate 1~5ms serial TX/RX
    time.sleep(0.003)


# === MEASUREMENT HELPERS ===


class Metrics:
    def __init__(self):
        self.picamera_count = 0
        self.serial_count = 0
        self.start_time = time.monotonic()

    def elapsed(self):
        return time.monotonic() - self.start_time


metrics = Metrics()

# === MODE 1: Thread-based ===


def thread_camera_worker():
    count = 0
    while metrics.elapsed() < TEST_DURATION_SEC:
        start = time.monotonic()
        mock_picamera_capture(CAMERA_FILENAME_TEMPLATE.format(count=count))
        metrics.picamera_count += 1
        count += 1
        elapsed = time.monotonic() - start
        sleep_time = max(0, CAMERA_INTERVAL_SEC - elapsed)
        time.sleep(sleep_time)


def thread_serial_worker(port_name):
    while metrics.elapsed() < TEST_DURATION_SEC:
        start = time.monotonic()
        mock_serial_communication(port_name)
        metrics.serial_count += 1
        elapsed = time.monotonic() - start
        sleep_time = max(0, SERIAL_INTERVAL_SEC - elapsed)
        time.sleep(sleep_time)


# === MODE 2: Asyncio + executor ===


async def async_camera_worker(executor):
    count = 0
    loop = asyncio.get_running_loop()
    while metrics.elapsed() < TEST_DURATION_SEC:
        start = time.monotonic()
        await loop.run_in_executor(
            executor,
            mock_picamera_capture,
            CAMERA_FILENAME_TEMPLATE.format(count=count),
        )
        metrics.picamera_count += 1
        count += 1
        elapsed = time.monotonic() - start
        await asyncio.sleep(max(0, CAMERA_INTERVAL_SEC - elapsed))


async def async_serial_worker():
    while metrics.elapsed() < TEST_DURATION_SEC:
        start = time.monotonic()
        mock_serial_communication("async_serial")
        metrics.serial_count += 1
        elapsed = time.monotonic() - start
        await asyncio.sleep(max(0, SERIAL_INTERVAL_SEC - elapsed))


async def run_async_mode():
    executor = ThreadPoolExecutor(max_workers=2)
    tasks = [async_camera_worker(executor)]
    tasks.extend([async_serial_worker() for _ in range(SERIAL_PORTS)])
    await asyncio.gather(*tasks)


# === RUNNER ===


def run_threads_mode():
    threads = [Thread(target=thread_camera_worker)]
    threads.extend(
        [
            Thread(target=thread_serial_worker, args=(f"serial_{i}",))
            for i in range(SERIAL_PORTS)
        ]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def monitor_cpu_usage():
    # Monitor CPU usage every second
    usage = []
    for _ in range(TEST_DURATION_SEC):
        cpu = psutil.cpu_percent(interval=1)
        usage.append(cpu)
    return usage


def run_test(mode_name, mode_func):
    print(f"\n--- Running mode: {mode_name} ---")
    global metrics
    metrics = Metrics()

    monitor_thread = Thread(target=lambda: monitor_cpu_usage(), daemon=True)
    monitor_thread.start()

    start_cpu = psutil.cpu_percent(interval=None)
    start_time = time.monotonic()

    if mode_name == "async":
        asyncio.run(mode_func())
    else:
        mode_func()

    elapsed = time.monotonic() - start_time
    end_cpu = psutil.cpu_percent(interval=None)

    avg_cpu = psutil.cpu_percent(interval=1)

    print(f"Elapsed time: {elapsed:.2f} sec")
    print(f"Picamera captures: {metrics.picamera_count}")
    print(f"Serial messages: {metrics.serial_count}")
    print(f"Average CPU usage: ~{avg_cpu}%")


# === MAIN ===
if __name__ == "__main__":
    run_test("threads", run_threads_mode)
    run_test("async", run_async_mode)
