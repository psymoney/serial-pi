from abc import ABC, abstractmethod
from typing import Protocol
from .connection import Method
from .frame import Frame
from .protocol import IProtocol


class Sensor(ABC):
    def __init__(self, frame, protocol, method):
        self.frame: Frame = frame
        self.protocol: IProtocol = protocol
        self.method: Method = method

    @property
    @abstractmethod
    def data(self) -> Frame:
        pass
