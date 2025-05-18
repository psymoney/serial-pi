from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from dataclasses import dataclass


T = TypeVar("T")


class Frame(ABC, Generic[T]):
    """
    sample:
    ```python
    @dataclass
    class SensorData(Frame['SensorData']):
        distance: int
        intensity: int
        temperature: int

        HEADER = b'\x57\x57'
        SIZE = 9

        @classmethod
        def parse(cls, data: bytes) -> 'SensorData':
            dist = data[2] | (data[3] << 8)
            flux = data[4] | (data[5] << 8)
            temp_raw = data[6] | (data[7] << 8)
            temp = (temp_raw >> 3) - 256
            return cls(distance=dist, intensity=flux, temperature=temp)

    ```
    """

    HEADER: bytes
    HEADER_LENGTH: int
    SIZE: int

    @classmethod
    @abstractmethod
    def parse(cls, data: bytes) -> T:
        pass

    @classmethod
    def validate(cls, data):
        if len(data) != cls.SIZE:
            raise ValueError(f"Invalid length: expected {cls.SIZE}, got {len(data)}")
        if not data.startswith(cls.HEADER):
            raise ValueError(f"Invalid header: expected {cls.HEADER!r}")
        chksum_idx = cls.SIZE - 1
        if not sum(data[:chksum_idx]) & 0xFF == data[chksum_idx]:
            raise ValueError("Invalid data: checksum error")

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        required_attrs = {"HEADER": bytes, "SIZE": int, "DATA": type}

        # validate member implementation
        for attr_name, expected_type in required_attrs.items():
            attr = getattr(cls, attr_name, None)
            if attr is None:
                raise NotImplementedError(f"`cls.{attr_name}` must be implemented!")

            if attr_name == "DATA":
                continue

            if not isinstance(attr, expected_type):
                raise TypeError(
                    f"`cls.{attr_name}` must be of type `{expected_type.__name__}`, got `{type(attr).__name__}`"
                )

        cls.HEADER_LENGTH = len(cls.HEADER)


@dataclass
class TFMPData(Frame["TFMPData"]):
    distance: int
    intensity: int
    temperature: int

    HEADER = b"\x59\x59"
    SIZE = 9
    DATA = tuple[int, int, int]

    @classmethod
    def parse(cls, data: bytes) -> "TFMPData":
        dist = data[2] | (data[3] << 8)
        flux = data[4] | (data[5] << 8)
        temp_raw = data[6] | (data[7] << 8)
        temp = (temp_raw >> 3) - 256
        return cls(distance=dist, intensity=flux, temperature=temp)


if __name__ == "__main__":
    print("it is main")
    data = b"\x59\x59\x12\x03\x00\x00\x00\x00\xc7"
    d = TFMPData.parse(data)
    print(d)
