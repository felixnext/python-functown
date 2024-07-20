"""Unit Tests for the functown.utils.stack_decorator module

Copyright (c) 2023, Felix Geilert
"""

import typing as tp
from inspect import signature
import pytest

from functown.utils import BaseDecorator, StackDecorator

# create two different BaseDecorators


class ArgDec(BaseDecorator):
    def __init__(self, name: str, **kwargs):
        super().__init__(None, [name], **kwargs)

        self._name = name

    def run(self, func, *args, **kwargs):
        item = f"dec: {self._name}"
        kwargs[self._name] = item
        return func(*args, **kwargs)


def test_stack_decorator():
    """Tests the StackDecorator"""
    # create the decorator
    dec = StackDecorator(
        [
            ArgDec("arg1"),
            ArgDec("arg2"),
        ]
    )

    # run the function
    @dec
    def test_func(my_param: str, arg1: str, arg2: str):
        return f"{my_param} {arg1} {arg2}"

    # validate the result
    result = test_func("foo")
    assert result == "foo dec: arg1 dec: arg2"

    # validate signature contains only my_param
    sig = signature(test_func)
    assert len(sig.parameters) == 1
    assert "my_param" in sig.parameters


@pytest.mark.asyncio
async def test_stack_decorator_async():
    """Tests the StackDecorator"""
    # create the decorator
    dec = StackDecorator(
        [
            ArgDec("arg1"),
            ArgDec("arg2"),
        ]
    )

    # run the function
    @dec
    async def test_func_as(my_param: str, arg1: str, arg2: str):
        return f"{my_param} {arg1} {arg2}"

    # validate the result
    result = await test_func_as("foo")
    assert result == "foo dec: arg1 dec: arg2"

    # validate signature contains only my_param
    sig = signature(test_func_as)
    assert len(sig.parameters) == 1
    assert "my_param" in sig.parameters


# --- Test Argument passing ---


class DecAddArg(BaseDecorator):
    def __init__(self, name: str, value: tp.Any, **kwargs):
        super().__init__(None, [name], **kwargs)

        self._name = name
        self._value = value

    def run(self, func, *args, **kwargs):
        kwargs[self._name] = self._value
        return func(*args, **kwargs)


class DecTestArg(BaseDecorator):
    def __init__(self, name: str, value: tp.Any, **kwargs):
        super().__init__(None, [name], **kwargs)

        self._name = name
        self._value = value

    def run(self, func, *args, **kwargs):
        # validate
        assert self._name in kwargs, f"Missing {self._name} in kwargs: {kwargs}"
        assert (
            kwargs[self._name] == self._value
        ), f"Wrong value for {self._name}, got {kwargs[self._name]}"

        return func(*args, **kwargs)


def test_stack_decorator_args():
    # test manually
    @DecAddArg("arg1", "value1")
    @DecAddArg("arg2", "value2")
    @DecTestArg("arg1", "value1")
    def test_func(my_param: str, arg1: str, arg2: str):
        return f"{my_param} {arg1} {arg2}"

    # validate the result
    result = test_func("foo")
    assert result == "foo value1 value2"

    # test with stack
    @StackDecorator(
        [
            DecAddArg("arg1", "value1"),
            DecAddArg("arg2", "value2"),
            DecTestArg("arg1", "value1"),
        ]
    )
    def test_func_stack(my_param: str, arg1: str, arg2: str):
        return f"{my_param} {arg1} {arg2}"

    # validate the result
    result = test_func_stack("foo")
    assert result == "foo value1 value2"
