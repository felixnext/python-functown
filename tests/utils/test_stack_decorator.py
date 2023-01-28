"""Unit Tests for the functown.utils.stack_decorator module

Copyright (c) 2023, Felix Geilert
"""

from inspect import signature

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
