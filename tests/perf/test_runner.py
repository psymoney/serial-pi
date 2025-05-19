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

from .conftest import Parameter
from tests.helper.subprocess_managers import (
    run_async_reader,
    run_blocking_reader,
    run_metric_monitor,
)


def test_async(reader_ports: list[str], test_id: str, test_params: Parameter):
    print(f"{reader_ports=} in test")
    with run_async_reader(*reader_ports, interval=test_params.interval) as reader_proc:
        with run_metric_monitor(
            reader_proc.pid,
            test_id,
            type=f"async_{test_params}",
        ):
            time.sleep(test_params.runtime)


def test_blocking(reader_ports: list[str], test_id: str, test_params: Parameter):
    with run_blocking_reader(*reader_ports, interval=test_params.interval) as reader_proc:
        with run_metric_monitor(
            reader_proc.pid,
            test_id,
            type=f"block_{test_params}",
        ):
            time.sleep(test_params.runtime)
