from time import time, sleep
from serial import Serial


# Buffer sizes
FRAME_SIZE = 9  # Size of one data frame = 9 bytes
frame = bytes(FRAME_SIZE)  # firmware version number

# System Error Status Condition
OK = 0  # no error
SERIAL_TIMEOUT = 1  # serial timeout
ERR_HEADER = 2  # no header found
ERR_CHECKSUM = 3  # checksum doesn't match
ERR_TIMEOUT = 4  # I2C timeout
ERR_DATA = 5  # reply from some system commands
SIGNAL_WEAK = 10  # Signal Strength ≤ 100
SIGNAL_STRONG = 11  # Signal Strength saturation
SIGNAL_FLOOD = 12  # Ambient Light saturation


HEADER = b"\x59\x59"


class TFMPSerial:
    FLAG: bool = True
    FRAME_SIZE: int = 9
    HEADER: bytes = b"\x59\x59"
    TIME_OUT: float = 0.01

    status: int
    distance: int = 0
    temperature: int
    signal_intensity: int

    def __init__(self, port, baudrate, header=None, frame_size=None):
        self._serial = Serial(port, baudrate)
        if frame_size:
            self.FRAME_SIZE = frame_size
        if header:
            self.HEADER = header

    def update(self):
        frame, status = self.read_frame()
        self.status = status
        if status != OK:
            return
        self.distance, self.temperature, self.signal_intensity, self.status = (
            self.parse_frame(frame)
        )

    def get_data(self):
        frame, status = self.read_frame()
        if status != OK:
            return None, None, None, status
        return self.parse_frame(frame)

    def read_frame(self) -> tuple[bytes, int]:
        deadline = time() + self.TIME_OUT

        while time() <= deadline:
            if self._serial.in_waiting < 2:
                sleep(0.001)
                continue

            # Step 1: 헤더 탐색
            first = self._serial.read(1)
            if first != b"\x59":
                continue
            second = self._serial.read(1)
            if second != b"\x59":
                continue

            # Step 2: 프레임 나머지 읽기
            rest = self._serial.read(self.FRAME_SIZE - 2)
            if len(rest) != self.FRAME_SIZE - 2:
                continue

            frame = b"\x59\x59" + rest

            # Step 3: 체크섬 확인
            if sum(frame[:8]) & 0xFF != frame[8]:
                return bytes(), ERR_CHECKSUM

            return frame, OK

        return bytes(), ERR_HEADER

    @staticmethod
    def parse_frame(frame: bytes) -> tuple[int, int, int, int]:
        """Parse a valid 9-byte frame into dist, flux, temp, and status."""
        dist = frame[2] | (frame[3] << 8)
        flux = frame[4] | (frame[5] << 8)
        temp_raw = frame[6] | (frame[7] << 8)
        temp = (temp_raw >> 3) - 256

        # Check for abnormal data
        if dist == -1:
            return dist, flux, temp, SIGNAL_WEAK
        elif flux == -1:
            return dist, flux, temp, SIGNAL_STRONG
        elif dist == -4:
            return dist, flux, temp, SIGNAL_FLOOD
        else:
            return dist, flux, temp, OK



