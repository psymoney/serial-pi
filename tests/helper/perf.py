from contextlib import contextmanager
import subprocess
import re
import time
import serial


@contextmanager
def virtual_serial_ports():
    try:
        proc = subprocess.Popen(
            ["socat", "-d", "-d", "PTY,raw,echo=0", "PTY,raw,echo=0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        ports = []
        for line in proc.stdout:
            match = re.search(r"PTY is (/dev/pts/\d+)", line)
            if match:
                ports.append(match.group(1))
            if len(ports) == 2:
                break
        print(f"{ports=}")
        yield ports  # 포트 두 개 반환

    finally:
        proc.terminate()
        proc.wait()


@contextmanager
def writer_process(writer_port):
    proc = subprocess.Popen(
        ["python3", "tests/helper/serial_writer.py", writer_port],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # writer가 데이터 쓰기 시작할 때까지 대기
    time.sleep(0.2)

    yield

    proc.terminate()
    proc.wait()


TIME_TO_PERFORM = 2


def test_serial_read_perf(reader_port):
    ser = serial.Serial(reader_port, 9600, timeout=1)

    count = 0
    start = time.time()

    while time.time() - start < TIME_TO_PERFORM:  # 2초 동안 읽기
        line = ser.readline()
        print(f"{line=}")
        if line:
            count += 1

    ser.close()

    print(f"\nRead {count} lines in {TIME_TO_PERFORM} seconds")
    assert count > 100  # 대략 초당 100줄 이상 도착해야 성공


@contextmanager
def reader_from_virt_ser_pair():
    with virtual_serial_ports() as ports:
        writer, reader = ports[0], ports[1]
        with writer_process(writer):
            yield reader


if __name__ == '__main__':
    with reader_from_virt_ser_pair() as reader:
        test_serial_read_perf(reader)

