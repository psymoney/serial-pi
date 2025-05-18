from abc import ABC, abstractmethod, ABCMeta
from time import time

from serial import Serial

from src.sensor.frame import Frame


class IProtocol(metaclass=ABCMeta):
    frame: Frame

    @abstractmethod
    def read(self) -> tuple[bytes, int]:
        pass


class BaseProtocol(IProtocol):
    serial: Serial

    def read(self) -> tuple[bytes, int]:
        data = self.serial.read(self.frame.SIZE)



class SynchronizationProtocol(BaseProtocol):
    TIMEOUT: float

    def read(self) -> tuple[bytes, int]:
        pass

    def _synchronize(self):
        deadline = time() + self.TIMEOUT
        while time() <= deadline:
            if self.serial.in_waiting < self.frame.HEADER_LENGTH:
            return self._read()
        raise BufferError("No Header Found!")

    def _read(self) -> tuple[bytes, int]:
        pass




if __name__ == '__main__':
    print('protocol main starts!')
