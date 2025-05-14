import os
from subprocess import Popen, PIPE, STDOUT
import re


def create_virtual_serial_pair():
    # socat을 subprocess로 실행
    proc = Popen(
        ["socat", "-d", "-d", "PTY,raw,echo=0", "PTY,raw,echo=0"],
        stdout=PIPE,
        stderr=STDOUT,
        universal_newlines=True,
    )

    ports = []
    # socat은 포트 경로를 stderr가 아닌 stdout으로 출력함
    for line in proc.stdout:
        print("SOCAT:", line.strip())  # 디버깅용
        match = re.search(r"PTY is (/dev/pts/\d+)", line)
        if match:
            ports.append(match.group(1))
        if len(ports) == 2:
            break

    return proc, ports[0], ports[1]


def cleanup_virtual_serial_pair(proc: Popen | None = None) -> bool:
    if proc is None:
        # kill all socat processes
        os.system("pkill socat")
        return True

    if not isinstance(proc, Popen):
        return False

    proc.terminate()
    proc.wait()

    return True


def is_pty_in_use(dev_path: str) -> bool:
    """
    check whether given dev_path is in use,
    then return `True` if it is,
    else return `False`
    """
    try:
        with open(dev_path):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    proc, reader, writer = create_virtual_serial_pair()

    print(f"{reader=}\n{writer=}")
    assert cleanup_virtual_serial_pair(proc)
    assert not is_pty_in_use(reader)
    assert not is_pty_in_use(writer)
