import time
from serial import Serial, SerialTimeoutException


def serial_write(
    port: str,
    baudrate: int = 9600,
    frame: bytes = b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7",
    interval: float = 0.001,
    use_monotonic: bool = False,
):
    with Serial(port, baudrate, timeout=1) as serial:
        try:
            if use_monotonic:
                next_time = time.monotonic()
                while True:
                    serial.write(frame)
                    serial.flush()

                    next_time += interval
                    sleep_time = next_time - time.monotonic()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        next_time = time.monotonic()
            else:
                while True:
                    serial.write(frame)
                    serial.flush()
                    time.sleep(interval)
        except SerialTimeoutException:
            print("Write timed out")
        except Exception as e:
            print('exception raised!', e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Serial Write Tool")
    parser.add_argument(
        "port", type=str, help="Serial port (e.g. COM3 or /dev/ttyUSB0)"
    )
    parser.add_argument(
        "-b", "--baudrate", type=int, default=9600, help="Baud rate (default: 9600)"
    )
    parser.add_argument(
        "-f",
        "--frame",
        type=lambda x: bytes.fromhex(x),
        default=b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7",
        help="Frame to send in hex format (e.g. '59' for 0x59)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=0.001,
        help="Interval in seconds (default: 0.001)",
    )
    parser.add_argument(
        "-m",
        "--monotonic",
        action="store_true",
        help="Use time.monotonic() loop for precise timing",
    )

    args = parser.parse_args()
    serial_write(args.port, args.baudrate, args.frame,
                 args.interval, args.monotonic)
