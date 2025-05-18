import asyncio
import uvloop
from src.async_pi.sensor import AsyncTFMPSerial


async def main(interval: float):
    sensor = await AsyncTFMPSerial.create(args.port, args.baudrate)
    while True:
        await sensor.update()
        await asyncio.sleep(interval)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Asyncio Based Serial Reader"
    )
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
        help="Interval in seconds (default: 0.01)",
    )

    args = parser.parse_args()

    uvloop.run(main(args.interval))
    # asyncio.run(main(args.interval))
