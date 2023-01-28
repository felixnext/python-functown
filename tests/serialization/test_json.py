""""Tests JSON serialization.

Copyright (c) 2023, Felix Geilert
"""

import json
from typing import Any

from azure.functions import HttpRequest, HttpResponse
import pytest

from functown.errors import RequestError
from functown.serialization import JsonResponse, JsonRequest


def test_json_response():
    """Tests JSON response serialization."""

    @JsonResponse
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert json.loads(res.get_body()) == {"hello": "world"}

    @JsonResponse()
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert json.loads(res.get_body()) == {"hello": "world"}

    @JsonResponse(headers={"X-My-Header": "My-Value"}, status_code=201)
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert res.status_code == 201
    assert res.headers["X-My-Header"] == "My-Value"
    assert json.loads(res.get_body()) == {"hello": "world"}


@pytest.mark.parametrize(
    "plain, enforce, data, mime, dumps, encode, key, error",
    [
        # basic (dumped)
        (
            True,
            False,
            {"foo": "bar"},
            "application/json",
            True,
            False,
            "foo",
            False,
        ),
        # basic (dumped, encoded)
        (
            True,
            False,
            {"foo": "bar"},
            "application/json",
            True,
            True,
            "foo",
            False,
        ),
        # basic (not dumped) - fail
        (
            True,
            False,
            {"foo": "bar"},
            "application/json",
            False,
            False,
            "foo",
            True,
        ),
        # invalid mime - fail
        (
            True,
            False,
            {"foo": "bar"},
            "text/plain",
            True,
            True,
            "foo",
            True,
        ),
        # not plain
        (
            False,
            True,
            {"foo": "bar"},
            "application/json",
            True,
            False,
            "foo",
            False,
        ),
        # not plain, invalid mime - fail
        (
            False,
            True,
            {"foo": "bar"},
            "text/plain",
            True,
            False,
            "foo",
            True,
        ),
        # not plain, invalid mime, no enforce
        (
            False,
            False,
            {"foo": "bar"},
            "text/plain",
            True,
            False,
            "foo",
            False,
        ),
        # invalid data type
        (True, False, [1, 2, 3], "application/json", False, False, "foo", True),
    ],
    ids=[
        "basic (dumped)",
        "basic (dumped, encoded)",
        "basic (not dumped) - fail",
        "invalid mime - fail",
        "not plain",
        "not plain, invalid mime - fail",
        "not plain, invalid mime, no enforce",
        "invalid data type",
    ],
)
def test_json_request(
    plain: bool,
    enforce: bool,
    data: Any,
    mime: str,
    dumps: bool,
    encode: bool,
    key: str,
    error: bool,
):
    """Tests JSON request deserialization."""

    if plain:
        dec = JsonRequest
    else:
        dec = JsonRequest(enfore_mime=enforce)

    @dec
    def main(req: HttpRequest, body: dict):
        return body[key]

    body_data = data
    if dumps:
        body_data = json.dumps(data)
    if encode:
        body_data = body_data.encode("utf-8")

    if error:
        with pytest.raises(RequestError):
            res = main(
                req=HttpRequest(
                    "GET",
                    "http://localhost",
                    body=body_data,
                    headers={"Content-Type": mime},
                )
            )
    else:
        res = main(
            req=HttpRequest(
                "GET",
                "http://localhost",
                body=body_data,
                headers={"Content-Type": mime},
            )
        )
        assert res == data[key]
