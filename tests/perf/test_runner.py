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
from typing import Generator
from datetime import datetime
from itertools import product

from tests.helper.create_summary import main
from tests.helper.subprocess_managers import (
    run_async_reader,
    run_blocking_reader,
    run_metric_monitor,
)

# test inputs
intervals: list[float] = [0.01]
runtimes: list[int] = [10]
loop: list = ["default", "uvloop"]

combinations = list(product(intervals, runtimes))
print(combinations)


@pytest.fixture(scope="function")
def test_id() -> Generator[str, None, None]:
    tid = datetime.now().strftime("%Y%m%d_%H%M%S")
    yield tid
    main(tid)


# @pytest.mark.skip
@pytest.mark.parametrize("interval,runtime", combinations)
def test_together(serial_writer, test_id: str, interval, runtime):
    reader_port, _ = serial_writer

    with run_async_reader(reader_port, interval) as reader_proc:
        print(f"{reader_port=}\nreader_pid={reader_proc.pid}")
        with run_metric_monitor(
            reader_proc.pid,
            test_id,
            type="async",
            # type=f"async_interval-{interval}_runtime-{runtime}",
        ):
            time.sleep(runtime)

    with run_blocking_reader(reader_port, interval) as reader_proc:
        print(f"{reader_port=}\nreader_pid={reader_proc.pid}")
        with run_metric_monitor(
            reader_proc.pid,
            test_id,
            type="block",
            # type=f"block_interval-{interval}_runtime-{runtime}",
        ):
            time.sleep(runtime)


@pytest.mark.skip
def test_blocking(serial_writer, test_id: str):
    reader_port, _ = serial_writer

    with run_blocking_reader(reader_port) as reader_proc:
        with run_metric_monitor(reader_proc.pid, test_id):
            time.sleep(15)
