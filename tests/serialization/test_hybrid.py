"""Tests the usage of Protobuf serialization.

Copyright (c) 2024, Felix Geilert
"""

import json

from azure.functions import HttpRequest, HttpResponse
import pytest

from functown.args import ContentTypes, HeaderEnum
from functown.errors import ArgError, RequestError
from functown.serialization import HybridProtoResponse
from .resources import example_pb2 as pb2


def test_hybridproto_response(json_data):
    """Tests protobuf response serialization."""
    # generate
    item = pb2.InformationList()
    info = item.infos.add()
    info.msg = "Hello World"
    info.id = 1
    info.score = 0.5
    for i in range(3):
        d = info.data.add()
        d.msg = f"Hello World {i}"
        d.type = pb2.Information.Importance.HIGH

    @HybridProtoResponse
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == item.SerializeToString()

    @HybridProtoResponse(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == item.SerializeToString()

    @HybridProtoResponse(headers={"X-My-Header": "My-Value"}, status_code=201)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.status_code == 201
    assert res.headers["X-My-Header"] == "My-Value"
    assert res.get_body() == item.SerializeToString()

    # validate errors
    @HybridProtoResponse(pb_class=pb2.Information)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=None))

    @HybridProtoResponse(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.Information:
        return info

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=None))

    # validate JSON serialization

    @HybridProtoResponse(pb_class=pb2.InformationList, allow_json=True)
    def main(req: HttpRequest) -> pb2.InformationList:
        return json_data

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == item.SerializeToString()
    body_item = pb2.InformationList()
    body_item.ParseFromString(res.get_body())
    assert body_item == item
