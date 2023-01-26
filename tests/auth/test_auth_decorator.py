"""Unit Tests for the Auth Decorator.

Copyright (c) 2023, Felix Geilert
"""

import pytest

from azure.functions import HttpRequest

from functown.auth import AuthHandler, Token
from functown.errors import TokenError


def test_auth_decorator(token_request: HttpRequest):
    @AuthHandler(["test.bar"])
    def test_func(request: HttpRequest, token: Token, **kwargs):
        # assert
        assert type(token) == Token
        assert token.user_id == "test"

    test_func(token_request)

    # test failure case
    @AuthHandler(["test.baz"])
    def test_func(request: HttpRequest, token: Token, **kwargs):
        pass

    with pytest.raises(TokenError):
        test_func(token_request)
