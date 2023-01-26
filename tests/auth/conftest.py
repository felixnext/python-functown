"""Fixtures for JWT Testing

Copyright (c) 2023, Felix Geilert
"""

import pytest

from azure.functions import HttpRequest
from jose import jwt


@pytest.fixture
def token_request():
    """Fixture for a JWT token."""
    # generate JWT token
    token = jwt.encode(
        {
            "sub": "test",
            "name": "test",
            "oid": "test",
            "scp": "test.foo test.bar",
            "exp": 9999999999,
        },
        "secret",
        algorithm="HS256",
    )

    # generate a request
    request = HttpRequest(
        method="GET",
        url="http://localhost",
        params={},
        route_params={},
        headers={"Authorization": f"Bearer {token}"},
        body=None,
    )

    return request
