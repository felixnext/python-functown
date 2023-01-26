"""Tests the decorator for the args module.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest

from functown import ArgsHandler, RequestArgHandler


def test_args_handler_params():
    req = HttpRequest(
        method="GET",
        url="https://example.com",
        params={"a": "1", "b": "2"},
        body=None,
    )

    @ArgsHandler()
    def test_func(req: HttpRequest, args: RequestArgHandler, **kwargs):
        assert args is not None
        assert args.get_query("a") == "1"
        assert args.get_body("a") is None
        assert args.get_query("b") == "2"

    test_func(req)


def test_args_handler_body():
    req = HttpRequest(
        method="POST",
        url="https://example.com",
        body=b'{"a": "1", "b": "2"}',
    )

    @ArgsHandler()
    def test_func(req: HttpRequest, args: RequestArgHandler, **kwargs):
        assert args is not None
        assert args.get_body("a") == "1"
        assert args.get_query("a") is None
        assert args.get_body("b") == "2"

    test_func(req)


def test_args_handler_body_query():
    req = HttpRequest(
        method="GET",
        url="https://example.com",
        params={"b": "2"},
        body=b'{"a": "1"}',
    )

    @ArgsHandler()
    def test_func(req: HttpRequest, args: RequestArgHandler, **kwargs):
        assert args is not None
        assert args.get_body_query("a") == "1"
        assert args.get_body_query("b") == "2"

    test_func(req)
