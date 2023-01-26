"""Some validation checks on the Args Handler.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest

from functown.args import RequestArgHandler


def test_reqargs_handler_params():
    req = HttpRequest(
        method="GET",
        url="https://example.com",
        params={"a": "1", "b": "2"},
        body=None,
    )
    args = RequestArgHandler(req)
    assert args is not None
    assert args.get_query("a") == "1"
    assert args.get_body("a") is None
    assert args.get_query("b") == "2"


def test_reqargs_handler_body():
    req = HttpRequest(
        method="POST",
        url="https://example.com",
        body=b'{"a": "1", "b": "2"}',
    )
    args = RequestArgHandler(req)
    assert args is not None
    assert args.get_body("a") == "1"
    assert args.get_query("a") is None
    assert args.get_body("b") == "2"


def test_reqargs_handler_body_query():
    req = HttpRequest(
        method="GET",
        url="https://example.com",
        params={"b": "2"},
        body=b'{"a": "1"}',
    )
    args = RequestArgHandler(req)
    assert args is not None
    assert args.get_body_query("a") == "1"
    assert args.get_body_query("b") == "2"
