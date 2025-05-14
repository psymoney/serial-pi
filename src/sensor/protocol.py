from src.sensor.status import ERR_DATA, ERR_CHECKSUM, OK
from time import time, sleep
from serial import Serial

from tests.helper.perf import TIME_TO_PERFORM

# Buffer sizes
TFMP_FRAME_SIZE = 9  # Size of one data frame = 9 bytes
TFMP_COMMAND_MAX = 8  # Longest command = 8 bytes
TFMP_REPLY_SIZE = 8  # Longest command reply = 8 bytes
# Buffers
frame = bytearray(TFMP_FRAME_SIZE)  # firmware version number
reply = bytearray(TFMP_REPLY_SIZE)  # firmware version number

# Timeout Limits for various functions
TFMP_MAX_READS = 20  # readData() sets SERIAL error
MAX_BYTES_BEFORE_HEADER = 20  # getData() sets HEADER error
MAX_ATTEMPTS_TO_MEASURE = 20

TFMP_DEFAULT_ADDRESS = 0x10  # default I2C slave address
# as hexidecimal integer
#
# System Error Status Condition
#
TFMP_READY = 0  # no error
TFMP_SERIAL = 1  # serial timeout
TFMP_HEADER = 2  # no header found
TFMP_CHECKSUM = 3  # checksum doesn't match
TFMP_TIMEOUT = 4  # I2C timeout
TFMP_PASS = 5  # reply from some system commands
TFMP_FAIL = 6  # "
TFMP_I2CREAD = 7
TFMP_I2CWRITE = 8
TFMP_I2CLENGTH = 9
TFMP_WEAK = 10  # Signal Strength ≤ 100
TFMP_STRONG = 11  # Signal Strength saturation
TFMP_FLOOD = 12  # Ambient Light saturation
TFMP_MEASURE = 13


HEADER = b"\x59\x59"


class ProtocolException(Exception):
    status: int


class InvalidDataException(ProtocolException):
    status = ERR_DATA

    def __init__(self, status: int = 5):
        self.status = status


class TFMPSerial:
    FLAG: bool = True
    FRAME_SIZE: int = 9
    HEADER: bytes = b"\x59\x59"
    TIME_OUT: float = 1.0

    def __init__(self, port, baudrate, header=None, frame_size=None):
        self._serial = Serial(port, baudrate)
        if frame_size:
            self.FRAME_SIZE = frame_size
        if header:
            self.HEADER = header

    def get_data(self):
        frame = self.read_frames()
        data = self.parse_frame(frame)
        return data

    def read_frames(self) -> bytes:
        while True:
            frame, status = self.read_frame()
            if status == OK:
                return frame
            else:
                print(f"{status=}, {self.FLAG=}")
                continue

    def read_frame(self) -> tuple[bytes | None, int]:
        deadline = time() + self.TIME_OUT

        # Flush stale bytes except the last frame
        if self._serial.in_waiting > TFMP_FRAME_SIZE:
            self._serial.read(self._serial.in_waiting - TFMP_FRAME_SIZE)

        while True:
            if time() > deadline:
                return None, TFMP_HEADER

            if self._serial.in_waiting >= TFMP_FRAME_SIZE:
                data = self._serial.read(TFMP_FRAME_SIZE)
                if data[0:2] == HEADER:
                    if sum(data[:8]) & 0xFF == data[8]:
                        return data, TFMP_READY
                    else:
                        return None, TFMP_CHECKSUM
                else:
                    self._serial.read(1)  # Skip a byte
            else:
                sleep(0.001)

    @staticmethod
    def parse_frame(frame: bytes):
        """Parse a valid 9-byte frame into dist, flux, temp, and status."""
        dist = frame[2] | (frame[3] << 8)
        flux = frame[4] | (frame[5] << 8)
        temp_raw = frame[6] | (frame[7] << 8)
        temp = (temp_raw >> 3) - 256

        # Check for abnormal data
        if dist == -1:
            return dist, flux, temp, TFMP_WEAK
        elif flux == -1:
            return dist, flux, temp, TFMP_STRONG
        elif dist == -4:
            return dist, flux, temp, TFMP_FLOOD
        else:
            return dist, flux, temp, TFMP_READY


class LidarData:
    distance: int
    temperature: int
    signal_intensity: int

    def __init__(self, data: bytes):
        self._validate_data(data)
        self.distance = data[2] + data[3] * 256
        self.temperature = 0
        self.signal_intensity = 0

    @classmethod
    def _validate_data(cls, data: bytes):
        if len(data) != 9:
            raise InvalidDataException
        if data[0] != 0x59 or data[1] != 0x59:
            raise InvalidDataException
        if not cls._verify_checksum(data):
            raise InvalidDataException(ERR_CHECKSUM)

    @staticmethod
    def _verify_checksum(data: bytes) -> bool:
        calc_checksum, checksum = sum(data[:8]) & 0xFF, data[8]
        return calc_checksum == checksum

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"distance={self.distance}, "
            f"signal_intensity={self.signal_intensity}, "
            f"temperature={self.temperature})"
        )


if __name__ == "__main__":
    a = LidarData(b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7")
    print(f"{a=}")

    from tests.helper import reader_from_virt_ser_pair, test_serial_read_perf

    TIME_TO_PERFORM = 2

    with reader_from_virt_ser_pair() as r:
        lidar = TFMPSerial(r, 9600)
        count = 0
        start = time()

        while time() - start < TIME_TO_PERFORM:  # 2초 동안 읽기
            data = lidar.get_data()
            count += 1
            print(f"{count}: {data=}")
        else:
            lidar.FLAG = False


