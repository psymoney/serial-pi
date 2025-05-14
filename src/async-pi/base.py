import serial_asyncio
import serial
import asyncio


class SerialProtocol(asyncio.Protocol):
    def __init__(self, port_name):
        self.port_name = port_name

    def connection_made(self, transport) -> None:
        self.transport = transport
        print(f"{self.port_name} connected")

    def data_received(self, data: bytes) -> None:
        print(f"{self.port_name} reseived: {data}")

    def connection_lost(self, exc: Exception | None) -> None:
        print(f"{self.port_name} disconnected")


async def open_serial(port, baudrate):
    loop = asyncio.get_running_loop()
    await serial_asyncio.create_serial_connection(
        loop, lambda: SerialProtocol(port), port, baudrate
    )


async def main():
    tasks = [
        open_serial("/dev/ttyUSB0", 9600),
        open_serial("/dev/ttyUSB0", 9600),
        open_serial("/dev/ttyUSB0", 9600),
    ]

    await asyncio.gather(*tasks)


asyncio.run(main())
