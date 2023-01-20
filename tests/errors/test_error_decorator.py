"""Tests the error decorator."""

from inspect import signature
import logging

import pytest

from azure.functions import HttpRequest, HttpResponse

from functown.errors import ErrorHandler


def test_error_decorator(caplog):
    """Tests the error decorator."""

    @ErrorHandler(debug=True)
    def test_function():
        logging.info("Hello World")

    # assert the function signature
    assert signature(test_function).parameters == {}

    # run function with caplog
    with caplog.at_level(logging.INFO):
        test_function()

    # assert the log
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Hello World"
