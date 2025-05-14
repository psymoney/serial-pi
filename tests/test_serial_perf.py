import serial
import time


TIME_TO_PERFORM = 2


def test_serial_read_perf(virtual_serial_ports, writer_process):
    reader_port = virtual_serial_ports[1]
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
