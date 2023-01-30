"""Tests the usage of Protobuf serialization.

Copyright (c) 2023, Felix Geilert
"""


from azure.functions import HttpRequest, HttpResponse
import pytest

from functown.serialization import ProtobufResponse, ProtobufRequest
from .resources import example_pb2 as pb2


def test_protobuf_response():
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

    @ProtobufResponse
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == item.SerializeToString()

    @ProtobufResponse(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == item.SerializeToString()

    @ProtobufResponse(headers={"X-My-Header": "My-Value"}, status_code=201)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert isinstance(res, HttpResponse)
    assert res.mimetype == "application/octet-stream"
    assert res.status_code == 201
    assert res.headers["X-My-Header"] == "My-Value"
    assert res.get_body() == item.SerializeToString()

    # validate errors
    @ProtobufResponse(pb_class=pb2.Information)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=None))

    @ProtobufResponse(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.Information:
        return info

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=None))

    # TODO: validate JSON serialization


def test_protobuf_request():
    """Tests protobuf request serialization."""
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

    @ProtobufRequest(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    res = main(
        req=HttpRequest("GET", "http://localhost", body=item.SerializeToString())
    )
    assert isinstance(res, pb2.InformationList)
    assert res == item

    # validate errors
    @ProtobufRequest(pb_class=pb2.Information)
    def main(req: HttpRequest) -> pb2.InformationList:
        return item

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=item.SerializeToString()))

    @ProtobufRequest(pb_class=pb2.InformationList)
    def main(req: HttpRequest) -> pb2.Information:
        return info

    with pytest.raises(ValueError):
        main(req=HttpRequest("GET", "http://localhost", body=item.SerializeToString()))
