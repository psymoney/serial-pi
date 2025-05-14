# conftest.py
import pytest
import subprocess
import re
import time


@pytest.fixture(scope="function")
def virtual_serial_ports():
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

    yield ports  # 포트 두 개 반환

    proc.terminate()
    proc.wait()


@pytest.fixture
def writer_process(virtual_serial_ports):
    writer_port = virtual_serial_ports[0]
    proc = subprocess.Popen(
        ["python3", "writer_process.py", writer_port],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # writer가 데이터 쓰기 시작할 때까지 대기
    time.sleep(0.2)
    yield

    proc.terminate()
    proc.wait()
