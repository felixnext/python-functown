""""Tests JSON serialization.

Copyright (c) 2023, Felix Geilert
"""

import json

from azure.functions import HttpRequest, HttpResponse

from functown.serialization import JsonResponse, JsonRequest


def test_json_response():
    """Tests JSON response serialization."""

    @JsonResponse
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert json.loads(res.get_body()) == {"hello": "world"}

    @JsonResponse()
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert json.loads(res.get_body()) == {"hello": "world"}

    @JsonResponse(headers={"X-My-Header": "My-Value"}, status_code=201)
    def main(req: HttpRequest) -> dict:
        return {"hello": "world"}

    res = main(HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/json"
    assert res.status_code == 201
    assert res.headers["X-My-Header"] == "My-Value"
    assert json.loads(res.get_body()) == {"hello": "world"}


def test_json_request():
    """Tests JSON request deserialization."""

    @JsonRequest
    def main(req: HttpRequest, body: dict):
        return body["hello"]

    res = main(
        HttpRequest("GET", "http://localhost", body=json.dumps({"hello": "world"}))
    )
    assert res == "world"

    @JsonRequest()
    def main(req: HttpRequest, body: dict):
        return body["hello"]

    res = main(
        HttpRequest(
            "GET",
            "http://localhost",
            body=json.dumps({"hello": "world"}).encode("utf-8"),
        )
    )
    assert res == "world"
