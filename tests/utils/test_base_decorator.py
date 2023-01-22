"""Test Case for the Base Decorator.

This will implement a sample decorator on top and use it as a function decorator.
It will also generate a logger
"""

from collections import OrderedDict
import logging
from inspect import signature, Parameter
from types import MappingProxyType

from azure.functions import HttpRequest
import pytest

from functown.utils import BaseDecorator


class SampleDecorator(BaseDecorator):
    def __init__(self, func=None, opt_param="default", **kwargs):
        super().__init__(func, **kwargs)
        self.opt_param = opt_param

    def run(self, func, *args, **kwargs):
        # check the exp level
        logging.info(
            f"Lvl {self.level}: Running with param: {self.opt_param} - outer: {self.is_first_decorator}"
        )
        return func(*args, **kwargs)


def test_base_decorator(caplog):
    """Test the base decorator."""

    # --- Pass Through ---
    @BaseDecorator()
    def test_func1():
        return 4

    assert test_func1() == 4

    @BaseDecorator()
    @BaseDecorator()
    def test_func2(i):
        return i

    assert test_func2(4) == 4

    # --- Sample Decorator ---
    @SampleDecorator(opt_param="test")
    def test_func3():
        logging.info("Running test_func")

    # execute and capture logs
    with caplog.at_level(logging.INFO):
        test_func3()

    # validate the logs
    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Lvl 0: Running with param: test - outer: True"
    assert caplog.records[1].message == "Running test_func"

    @SampleDecorator(opt_param="var1")
    @SampleDecorator(opt_param="var2")
    def test_func4(arg1, arg2):
        logging.info(f"Running test_func: {arg1} {arg2}")

    # execute and capture logs
    with caplog.at_level(logging.INFO):
        test_func4("test", "test2")

    # validate the logs
    assert len(caplog.records) == 5
    assert caplog.records[2].message == "Lvl 1: Running with param: var1 - outer: True"
    assert caplog.records[3].message == "Lvl 0: Running with param: var2 - outer: False"
    assert caplog.records[4].message == "Running test_func: test test2"


def test_base_decorator_signature():
    """Tests the error decorator."""

    # --- SIMPLE FUNCTION ---
    @BaseDecorator()
    def test_function():
        logging.info("Hello World")

    assert signature(test_function).parameters == {}

    # --- PARAMETER FUNCTION ---
    @BaseDecorator()
    def test_function2(req: HttpRequest):
        logging.info("Hello World")

    prox = MappingProxyType(
        OrderedDict(
            req=Parameter(
                "req",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=HttpRequest,
                default=Parameter.empty,
            )
        )
    )
    assert signature(test_function2).parameters == prox

    # --- VAR ARGS FUNCTION ---
    @BaseDecorator()
    def test_function3(req: HttpRequest, *params, **kwargs):
        logging.info("Hello World")

    assert signature(test_function3).parameters == prox

    # --- VAR ARGS AND DEFAULT FUNCTION ---
    @BaseDecorator()
    def test_function4(req: HttpRequest, default: int = 10, *params, **kwargs):
        logging.info("Hello World")

    prox_def = MappingProxyType(
        OrderedDict(
            req=Parameter(
                "req",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=HttpRequest,
                default=Parameter.empty,
            ),
            default=Parameter(
                "default",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=int,
                default=10,
            ),
        )
    )
    assert signature(test_function4).parameters == prox_def

    # --- MULTIPLE DECORATORS ---
    @BaseDecorator()
    @BaseDecorator()
    def test_function5(req: HttpRequest, *foo, **bar):
        logging.info("Hello World")

    assert signature(test_function5).parameters == prox
