from time import sleep, time

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
    TIME_OUT: float = 0.01

    status: int
    distance: int
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

        # Flush stale bytes except the last frame
        if self._serial.in_waiting > FRAME_SIZE:
            self._serial.read(self._serial.in_waiting - FRAME_SIZE)
        count = 0
        # repeat during deadline
        while time() <= deadline:
            count += 1
            print(f"{count=}")
            if self._serial.in_waiting >= FRAME_SIZE:
                data = self._serial.read(FRAME_SIZE)
                if data[0:2] == HEADER:
                    count = 0
                    if sum(data[:8]) & 0xFF == data[8]:
                        return data, OK
                    else:
                        return bytes(), ERR_CHECKSUM

                    # header does not match rotate position by 1 byte
                else:
                    self._serial.read(1)
                # wait until data will be enough
            else:
                sleep(0.001)

        return frame, ERR_HEADER

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

    TIME_TO_PERFORM = 2

