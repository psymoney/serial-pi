import sys
import asyncio
import uvloop
from src.async_pi.sensor import AsyncTFMPSerial


async def loop_sensor(port: str, baudrate: int, interval: float):
    sensor = await AsyncTFMPSerial.create(port, baudrate)
    while True:
        await sensor.update()
        await asyncio.sleep(interval)


async def main(ports: list[str], baudrate: int, interval: float):
    tasks = [loop_sensor(port, baudrate, interval) for port in ports]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Asyncio Based Serial Reader")
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
        help="Interval in seconds (default: 0.01)",
    )
    parser.add_argument("-t", "--type", type=str, default="uvloop")

    args = parser.parse_args()

    coro = main(args.port, args.baudrate, args.interval)

    if (type_ := args.type) == "uvloop":
        uvloop.run(coro)
    elif type_ == "default":
        loop = asyncio.get_event_loop_policy().get_event_loop()
        assert not isinstance(loop, asyncio.BaseEventLoop), (
            "default event loop is not of `BaseEventLoop`"
        )
        asyncio.run(coro)
    else:
        sys.exit("no running type is matching! sensor processor is not working")
