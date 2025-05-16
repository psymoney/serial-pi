import pytest
from typing import Generator

from tests.helper.subprocess_managers import (
    run_metric_monitor,
    run_serial_writer,
    run_virtual_serial_pair,
)


@pytest.fixture
def virtual_serial_ports() -> Generator[tuple[str, str], None, None]:
    with run_virtual_serial_pair() as (_, reader, writer):
        yield reader, writer


@pytest.fixture
def serial_writer(virtual_serial_ports) -> Generator[tuple[str, int], None, None]:
    writer, reader = virtual_serial_ports
    with run_serial_writer(writer) as proc:
        yield reader, proc.pid


@pytest.fixture
def monitor_on_writer(serial_writer):
    reader, pid = serial_writer
    with run_metric_monitor(pid):
        yield reader
