"""Test Case for the Base Decorator.

This will implement a sample decorator on top and use it as a function decorator.
It will also generate a logger
"""

import logging

from functown.utils import BaseDecorator


class SampleDecorator(BaseDecorator):
    def __init__(self, func=None, opt_param="default", **kwargs):
        super().__init__(func, **kwargs)
        self.opt_param = opt_param

    def run(self, func, *args, **kwargs):
        logging.info(f"Running with param: {self.opt_param}")
        return func(*args, **kwargs)


def test_base_decorator(caplog):
    """Test the base decorator."""

    @SampleDecorator(opt_param="test")
    def test_func():
        logging.info("Running test_func")

    # execute and capture logs
    with caplog.at_level(logging.INFO):
        test_func()

    # validate the logs
    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Running with param: test"
    assert caplog.records[1].message == "Running test_func"

    @SampleDecorator(opt_param="var1")
    @SampleDecorator(opt_param="var2")
    def test_func2(arg1, arg2):
        logging.info(f"Running test_func: {arg1} {arg2}")

    # execute and capture logs
    with caplog.at_level(logging.INFO):
        test_func2("test", "test2")

    # validate the logs
    assert len(caplog.records) == 5
    assert caplog.records[2].message == "Running with param: var1"
    assert caplog.records[3].message == "Running with param: var2"
    assert caplog.records[4].message == "Running test_func: test test2"
