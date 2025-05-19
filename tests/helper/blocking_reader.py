import sys
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from src.blocking_pi.sensor import TFMPSerial


def loop_sensor(port: str, baudrate: int, interval: float):
    sensor = TFMPSerial(port, baudrate=baudrate)
    while True:
        sensor.update()
        time.sleep(interval)


def run_in_naive_thread(ports: list[str], baudrate: int, interval: float):
    threads = []
    for port in ports:
        thread = Thread(
            target=loop_sensor, args=(port, baudrate, interval), daemon=True
        )
        thread.start()
        threads.append(thread)
    return threads


def run_in_thread_pool(
    ports: list[str], baudrate: int, interval: float, pool_size: int | None = None
):
    with ThreadPoolExecutor(max_workers=pool_size if pool_size else len(ports)) as pool:
        for port in ports:
            pool.submit(loop_sensor, port, baudrate, interval)

        yield


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blocking IO Based Serial Reader")
    parser.add_argument(
        "port", type=str, nargs="+", help="Serial port (e.g. COM3 or /dev/ttyUSB0)"
    )
    parser.add_argument(
        "-b", "--baudrate", type=int, default=9600, help="Baud rate (default: 9600)"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=0.01,
        help="Interval in seconds (default: 0.001)",
    )
    parser.add_argument("-t", "--type", type=str, default="naive")

    args = parser.parse_args()

    if (type_ := args.type) == "pool":
        run_in_thread_pool(args.port, args.baudrate, args.interval)
    elif type_ == "naive":
        run_in_naive_thread(args.port, args.baudrate, args.interval)
    else:
        sys.exit("no running type is matching! sensor processor is not working")

    while True:
        time.sleep(1)
