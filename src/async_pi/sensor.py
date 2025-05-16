from typing import Self
import asyncio
from time import time
from serial_asyncio import open_serial_connection


FRAME_SIZE = 9  # 고정 프레임 크기
HEADER = b"\x59\x59"

OK = 0
ERR_HEADER = 2
ERR_CHECKSUM = 3
SIGNAL_WEAK = 10
SIGNAL_STRONG = 11
SIGNAL_FLOOD = 12


class AsyncTFMPSerial:
    TIME_OUT = 0.01

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer

        self.FRAME_SIZE = FRAME_SIZE
        self.HEADER = HEADER

        self.status = None
        self.distance = 0
        self.temperature = 0
        self.signal_intensity = 0

    @classmethod
    async def create(cls, port: str, baudrate: int = 9600) -> Self:
        reader, writer = await open_serial_connection(url=port, baudrate=baudrate)
        return cls(reader, writer)

    async def update(self):
        frame, status = await self.read_frame()
        self.status = status
        if status != OK:
            return
        self.distance, self.temperature, self.signal_intensity, self.status = (
            self.parse_frame(frame)
        )

    async def get_data(self):
        frame, status = await self.read_frame()
        if status != OK:
            return None, None, None, status
        return self.parse_frame(frame)

    async def read_frame(self) -> tuple[bytes, int]:
        deadline = time() + self.TIME_OUT

        while time() <= deadline:
            # 헤더 찾기: 2바이트 읽기
            try:
                first = await asyncio.wait_for(
                    self._reader.readexactly(1), timeout=self.TIME_OUT
                )
                if first != b"\x59":
                    continue
                second = await asyncio.wait_for(
                    self._reader.readexactly(1), timeout=self.TIME_OUT
                )
                if second != b"\x59":
                    continue
            except asyncio.TimeoutError:
                break

            # 나머지 바이트 읽기
            try:
                rest = await asyncio.wait_for(
                    self._reader.readexactly(self.FRAME_SIZE - 2), timeout=self.TIME_OUT
                )
            except asyncio.TimeoutError:
                break

            frame = b"\x59\x59" + rest

            # 체크섬 확인
            if sum(frame[:8]) & 0xFF != frame[8]:
                return bytes(), ERR_CHECKSUM

            return frame, OK

        return bytes(), ERR_HEADER

    @staticmethod
    def parse_frame(frame: bytes) -> tuple[int, int, int, int]:
        dist = frame[2] | (frame[3] << 8)
        flux = frame[4] | (frame[5] << 8)
        temp_raw = frame[6] | (frame[7] << 8)
        temp = (temp_raw >> 3) - 256

        if dist == -1:
            return dist, flux, temp, SIGNAL_WEAK
        elif flux == -1:
            return dist, flux, temp, SIGNAL_STRONG
        elif dist == -4:
            return dist, flux, temp, SIGNAL_FLOOD
        else:
            return dist, flux, temp, OK


async def main(reader_port: str, baudrate: int = 9600):
    # reader, _ = await open_serial_connection(url=reader_port, baudrate=9600)

    sensor = await AsyncTFMPSerial.create(reader_port, 9600)
    while True:
        await sensor.update()
        print(sensor.distance, sensor.status)
        await asyncio.sleep(0.01)
        # print(line)
        # print("Received: ", line)
        #


if __name__ == "__main__":
    from tests.helper.subprocess_managers import (
        run_virtual_serial_pair,
        run_serial_writer,
    )

    loop = asyncio.get_event_loop()

    with run_virtual_serial_pair() as (_, reader, writer):
        with run_serial_writer(writer):
            asyncio.run(main(reader))
