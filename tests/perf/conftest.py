from dataclasses import dataclass, field, fields
import pytest
from typing import Generator
from datetime import datetime
from pathlib import Path

from tests.helper.create_summary import summarize_results
from tests.helper.subprocess_managers import (
    run_metric_monitor,
    run_serial_writer,
    run_serial_writers,
    run_virtual_serial_pair,
    run_virtual_serial_pairs,
)


# test inputs
num_sensors = [1, 2, 4]
intervals: list[float] = [0.1, 0.01, 0.005]
runtimes: list[int] = [5]
loop: list = ["default", "uvloop"]


@pytest.fixture(params=num_sensors)
def sensors(request) -> int:
    return request.param


@pytest.fixture(params=intervals)
def interval(request) -> float:
    return request.param


@pytest.fixture(params=runtimes)
def runtime(request) -> int:
    return request.param


@pytest.fixture(scope="module")
def test_id() -> Generator[str, None, None]:
    tid = datetime.now().strftime("%Y%m%d_%H%M%S")
    yield tid
    print("=" * 100)
    print("SUMMARIZE RESULTS")
    print("=" * 100)
    summarize_results(Path(__file__).parent / "results" / tid)


@dataclass
class Parameter:
    sensors: int = field(metadata={"tagged": True})
    interval: float = field(metadata={"tagged": True})
    runtime: int = field(metadata={"tagged": True})

    def __repr__(self) -> str:
        return "_".join(
            f"{f.name}-{getattr(self, f.name)}"
            for f in fields(self)
            if f.metadata.get("tagged")
        )


@pytest.fixture
def test_params(sensors, interval, runtime) -> Parameter:
    return Parameter(sensors=sensors, interval=interval, runtime=runtime)


@pytest.fixture
def virtual_serial_ports(sensors: int) -> Generator[list[tuple[str, str]], None, None]:
    with run_virtual_serial_pairs(sensors) as pairs:
        yield [(w, r) for (_, w, r) in pairs]


@pytest.fixture
def virtual_serial_port() -> Generator[tuple[str, str], None, None]:
    with run_virtual_serial_pair() as (_, w, r):
        yield w, r


@pytest.fixture
def serial_writer(
    virtual_serial_port, test_params
) -> Generator[tuple[str, int], None, None]:
    writer, reader = virtual_serial_port
    with run_serial_writer(writer, interval=test_params.interval) as proc:
        yield reader, proc.pid


@pytest.fixture
def serial_writers(
    virtual_serial_ports: list[tuple[str, str]], interval: int
) -> Generator[list[tuple[str, int]], None, None]:
    with run_serial_writers(
        [w for w, _ in virtual_serial_ports], interval=interval
    ) as writers:
        yield [(r, w.pid) for (_, r), w in zip(virtual_serial_ports, writers)]


@pytest.fixture
def reader_ports(serial_writers: list[tuple[str, int]]) -> list[str]:
    return [port for port, _ in serial_writers]


@pytest.fixture
def monitor_on_writer(serial_writer):
    reader, pid = serial_writer
    with run_metric_monitor(pid):
        yield reader
