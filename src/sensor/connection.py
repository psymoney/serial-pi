from abc import ABC, abstractmethod


class Method(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self):
        pass


class AsyncMethod(Method):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def read(self):
        pass

    @abstractmethod
    async def write(self):
        pass


class Serial(Method):
    pass


class AsyncSerial(AsyncMethod):
    pass
