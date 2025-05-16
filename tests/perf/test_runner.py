"""
TEST matrix

variables:
    1. # of sensors (not yet)
    2. sensor read interval
    3. data processing interval
    4. camera read interval
    5. camera output size
    6. # of network communications
    7. size of avg. network packet
"""

import pytest
import time
from datetime import datetime
from tests.helper.subprocess_managers import (
    run_async_reader,
    run_blocking_reader,
    run_metric_monitor,
)


@pytest.fixture(scope="function")
def test_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def test_together(serial_writer, test_id: str):
    interval = 0.001
    runtime = 30
    reader_port, _ = serial_writer

    with run_blocking_reader(reader_port, interval) as reader_proc:
        with run_metric_monitor(reader_proc.pid, test_id):
            time.sleep(runtime)
    with run_async_reader(reader_port, interval) as reader_proc:
        with run_metric_monitor(reader_proc.pid, test_id, type="async"):
            time.sleep(runtime)


@pytest.mark.skip
def test_blocking(serial_writer, test_id: str):
    reader_port, _ = serial_writer

    with run_blocking_reader(reader_port) as reader_proc:
        with run_metric_monitor(reader_proc.pid, test_id):
            time.sleep(15)
