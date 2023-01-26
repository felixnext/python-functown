"""Test the JWT Token validation functions.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest

from functown.auth import decode_token, verify_user, Token


def test_decode_token(token_request: HttpRequest):
    """Test the decoding of a token."""
    # decode the token
    decoded = decode_token(token_request.headers, verify=False)
    assert type(decoded) == Token


def test_verify_user(token_request: HttpRequest):
    """Test the verification of a user."""
    # verify the user
    token = verify_user(token_request, ["test.bar"], verify=False)
    assert type(token) == Token
