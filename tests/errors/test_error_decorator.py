"""Tests the error decorator."""

from collections import OrderedDict
from inspect import Parameter, signature
import json
import logging
from types import MappingProxyType
from typing import List

import pytest

from azure.functions import HttpRequest, HttpResponse

from functown.errors import ErrorHandler, TokenError, RequestError
from functown.utils import BaseDecorator


def test_error_decorator_signature():
    """Tests the error decorator."""

    # --- SIMPLE FUNCTION ---
    @ErrorHandler(debug=True)
    def test_function():
        logging.info("Hello World")

    assert signature(test_function).parameters == {}

    # --- PARAMETER FUNCTION ---
    @ErrorHandler(debug=True, log_all_errors=True)
    def test_function2(req: HttpRequest):
        logging.info("Hello World")

    # assert that the signature of the inner function is unchanged
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

    # --- KWARGS FUNCTION ---
    @ErrorHandler(debug=True, log_all_errors=True)
    def test_function3(req: HttpRequest, *params, **kwargs):
        logging.info("Hello World")

    assert signature(test_function3).parameters == prox

    # test multiple decorators
    @ErrorHandler(debug=False, log_all_errors=False)
    @ErrorHandler(debug=True, log_all_errors=True)
    def test_function4(req: HttpRequest, *foo, **bar):
        logging.info("Hello World")

    assert signature(test_function4).parameters == prox

    # --- TEST LOGGER ---
    @ErrorHandler(debug=False, log_all_errors=False)
    @ErrorHandler(debug=True, log_all_errors=True, enable_logger=True, return_logs=True)
    def test_function5(
        req: HttpRequest, logger: logging.Logger, logs: List[str], *foo, **bar
    ):
        logging.info("Hello World")

    assert signature(test_function5).parameters == prox

    @ErrorHandler(debug=True, log_all_errors=True, enable_logger=True, return_logs=True)
    @ErrorHandler(debug=False, log_all_errors=False)
    def test_function6(
        req: HttpRequest, logger: logging.Logger, logs: List[str], *foo, **bar
    ):
        logging.info("Hello World")

    assert signature(test_function6).parameters == prox


@pytest.mark.skip
def test_error_decorator_logs(caplog):
    """Tests if the error decorator logs correctly."""
    # --- GENERAL LOGGING ---
    @ErrorHandler(debug=True)
    def test_function():
        logging.info("Hello World")
        logging.error("Hello Error")

    # run function with caplog
    with caplog.at_level(logging.INFO):
        test_function()

    # assert the log
    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Hello World"
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[1].message == "Hello Error"
    assert caplog.records[1].levelname == "ERROR"

    # --- CUSTOM LOGGER ---
    @ErrorHandler(debug=True, enable_logger=True)
    def test_function2(logger: logging.Logger):
        logger.info("Hello World 2")
        logger.error("Hello Error 2")

    # run function with caplog
    with caplog.at_level(logging.INFO):
        test_function2()

    # assert the log
    assert len(caplog.records) == 4
    assert caplog.records[2].message == "Hello World 2"
    assert caplog.records[2].levelname == "INFO"
    assert caplog.records[3].message == "Hello Error 2"
    assert caplog.records[3].levelname == "ERROR"

    # --- None first item ---
    @BaseDecorator()
    @ErrorHandler(debug=True, enable_logger=True)
    def test_function3(logger: logging.Logger):
        logger.info("Hello World 3")
        logger.error("Hello Error 3")

    # run function with caplog
    with caplog.at_level(logging.INFO):
        test_function3()

    # assert the log
    assert len(caplog.records) == 7
    assert caplog.records[4].message == (
        "It is advised to use ErrorHandler as the first decorator, "
        "it is currently at the 0 level. (Should be 1)"
    )
    assert caplog.records[4].levelname == "WARNING"
    assert caplog.records[5].message == "Hello World 3"
    assert caplog.records[5].levelname == "INFO"
    assert caplog.records[6].message == "Hello Error 3"
    assert caplog.records[6].levelname == "ERROR"


@pytest.mark.parametrize(
    "exc,method,body,return_errors",
    [
        (None, "GET", None, False),
        (None, "POST", None, False),
        (None, "POST", {"foo": "bar"}, False),
        (ValueError, "GET", None, False),
        (ValueError, "GET", None, True),
        (TokenError, "GET", None, False),
        (TokenError, "GET", None, True),
    ],
    ids=[
        "GET",
        "POST",
        "POST_BODY",
        "GET_VALUE_ERROR",
        "GET_VALUE_ERROR_RETURN_ERRORS",
        "GET_TOKEN_ERROR",
        "GET_TOKEN_ERROR_RETURN_ERRORS",
    ],
)
def test_error_decorator_response(caplog, exc, method, body, return_errors):
    # generate a sample request
    req = HttpRequest(
        method=method,
        url="http://localhost:7071/api/test",
        params={},
        headers={},
        body=body,
        route_params={},
    )

    # run through a decorated function
    @ErrorHandler(debug=True, log_all_errors=True, return_errors=return_errors)
    def test_function(req: HttpRequest, *params, **kwargs):
        logging.info("Hello World")
        logging.error("Hello Error")
        if body is not None:
            logging.warning(f"Body: {body}")
        if exc is not None:
            raise exc("Hello Exception", 500) if issubclass(exc, RequestError) else exc(
                "Hello Exception"
            )
        return HttpResponse("Hello World", mimetype="text/plain", status_code=200)

    # run function with caplog
    with caplog.at_level(logging.INFO):
        resp = test_function(req)

    # assert the log
    count = 2
    if body is not None:
        count += 1
    if exc is not None:
        count += 5
    assert len(caplog.records) == count
    assert caplog.records[0].message == "Hello World"
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[1].message == "Hello Error"
    assert caplog.records[1].levelname == "ERROR"
    pos = 2
    if body is not None:
        assert caplog.records[pos].message == f"Body: {body}"
        assert caplog.records[pos].levelname == "WARNING"
        pos += 1
    if exc is not None:
        if issubclass(exc, RequestError):
            assert caplog.records[pos].message == (exc.__name__)
            assert (
                caplog.records[pos + 1].message
                == f"Error ({str(exc)}): Error (500): Hello Exception (Obj: Hello Exception)"
            )
        else:
            assert caplog.records[pos].message == "General Error"
            assert (
                caplog.records[pos + 1].message
                == f"Error ({str(exc)}): Hello Exception (Obj: Hello Exception)"
            )
        assert caplog.records[pos].levelname == "ERROR"
        assert caplog.records[pos + 1].levelname == "ERROR"
        assert caplog.records[pos + 2].message == "Trace:"
        assert caplog.records[pos + 3].message == (
            f"- error_decorator.py:122:{'163' if exc == TokenError else '172'}"
            " - Vars: ('self', 'func', 'args', 'kwargs', 'logs', 'logger', 'ex')"
        )
        assert (
            caplog.records[pos + 4].message
            == "- test_error_decorator.py:175:182 - Vars: ('req', 'params', 'kwargs')"
        )
        pos += 4

    # assert the response
    assert type(resp) == HttpResponse
    if exc is not None:
        assert resp.status_code == 500
        if return_errors:
            assert resp.mimetype == "application/json"
            body = json.loads(resp.get_body())
            assert len(body) == 4
            assert (
                body["value"] == "Error (500): Hello Exception"
                if issubclass(exc, TokenError)
                else "Hello Exception"
            )
            assert (
                body["user_message"] == "Hello Exception"
                if issubclass(exc, TokenError)
                else "This function executed unsuccessfully"
            )
        else:
            assert resp.mimetype == "text/plain"
    else:
        assert resp.status_code == 200
        assert resp.mimetype == "text/plain"
