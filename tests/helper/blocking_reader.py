import time
from src.blocking_pi.sensor import TFMPSerial


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Blocking IO Based Serial Reader")
    parser.add_argument(
        "port", type=str, help="Serial port (e.g. COM3 or /dev/ttyUSB0)"
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

    args = parser.parse_args()

    sensor = TFMPSerial(args.port, args.baudrate)
    while True:
        d = sensor.get_data()
        time.sleep(args.interval)
