import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
import time
import re
from contextlib import ExitStack, contextmanager
from typing import Iterator, Generator
from datetime import datetime


def wait_for_writer_ready(port: str, timeout: float = 3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(port):
            try:
                with open(port, "wb"):
                    return True
            except OSError:
                return True  # 이미 누군가 열었음
        time.sleep(0.05)
    raise RuntimeError("Writer did not open port in time")


@contextmanager
def run_serial_writers(
    writer_ports: list[str], interval: float = 0.01
) -> Generator[list[Popen], None, None]:
    writers = []

    with ExitStack() as stack:
        for _, port in enumerate(writer_ports):
            writer = stack.enter_context(run_serial_writer(port, interval=interval))
            writers.append(writer)
        yield writers


@contextmanager
def run_serial_writer(
    writer_port,
    baudrate: int = 9600,
    frame: bytes = b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7",
    interval: float = 0.01,
    monotonic: bool = False,
):
    print("start serial writer")

    args = [
        "python3",
        "tests/helper/serial_writer.py",
        writer_port,
        "-b",
        str(baudrate),
        "-f",
        frame.hex(),
        "-i",
        str(interval),
    ]

    if monotonic:
        args.append("-m")

    proc = subprocess.Popen(
        args,
        # stdout=subprocess.DEVNULL,
        # stderr=subprocess.PIPE,
    )
    try:
        wait_for_writer_ready(writer_port, timeout=2.0)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


@contextmanager
def run_async_reader(*reader_ports, interval: float = 0.01):
    print("start async reader process")
    proc = subprocess.Popen(
        [
            "python3",
            "-m",
            "tests.helper.async_reader",
            *reader_ports,
            "-i",
            str(interval),
        ]
    )
    try:
        for reader_port in reader_ports:
            wait_for_writer_ready(reader_port, timeout=2.0)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


@contextmanager
def run_blocking_reader(*reader_ports, interval: float = 0.01):
    print("start blocking reader process")
    proc = subprocess.Popen(
        [
            "python3",
            "-m",
            "tests.helper.blocking_reader",
            *reader_ports,
            "-i",
            str(interval),
        ]
    )
    try:
        for reader_port in reader_ports:
            wait_for_writer_ready(reader_port, timeout=2.0)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


@contextmanager
def run_metric_monitor(target_pid, test_id: str | None = None, type: str = "blocking"):
    if test_id is None:
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_name = type + ".log"
    print("start monitor process")
    proc = subprocess.Popen(
        [
            "python3",
            "tests/helper/metric_monitor.py",
            "-p",
            str(target_pid),
            "--id",
            test_id,
            "-f",
            file_name,
        ]
    )
    time.sleep(0.1)

    yield proc

    proc.terminate()
    proc.wait()


@contextmanager
def run_virtual_serial_pairs(
    count: int,
) -> Generator[list[tuple[Popen, str, str]], None, None]:
    pairs = []

    with ExitStack() as stack:
        for i in range(count):
            pair = stack.enter_context(run_virtual_serial_pair())
            pairs.append(pair)
        yield pairs


@contextmanager
def run_virtual_serial_pair() -> Iterator[tuple[Popen, str, str]]:
    print("start virtual serial pair")
    # socat을 subprocess로 실행
    proc = Popen(
        ["socat", "-d", "-d", "PTY,raw,echo=0", "PTY,raw,echo=0"],
        stdout=PIPE,
        stderr=STDOUT,
        universal_newlines=True,
    )

    ports = []
    timeout = time.monotonic() + 5

    assert proc.stdout is not None

    # socat은 포트 경로를 stderr가 아닌 stdout으로 출력함
    for line in proc.stdout:
        print("SOCAT:", line.strip())  # 디버깅용
        match = re.search(r"PTY is (/dev/pts/\d+)", line)
        if match:
            ports.append(match.group(1))
        if len(ports) == 2:
            break
        if time.monotonic() > timeout:
            proc.terminate()
            raise RuntimeError("Timeout: socat did not create PTYs in time.")
    print(f"socat pid={proc.pid}\nport0={ports[0]}\nport1={ports[1]}")

    try:
        # close logging pipe
        # without this serial port does not work
        # after some write operations
        proc.stdout.close()
        yield proc, ports[0], ports[1]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
