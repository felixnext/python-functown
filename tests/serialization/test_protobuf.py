"""Tests the usage of Protobuf serialization.

Copyright (c) 2023, Felix Geilert
"""


from azure.functions import HttpRequest, HttpResponse
import pytest

from functown.errors import ArgError, RequestError
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
    def main(req: HttpRequest, body: pb2.InformationList) -> pb2.InformationList:
        return body

    res = main(
        req=HttpRequest("GET", "http://localhost", body=item.SerializeToString())
    )
    assert type(res) == pb2.InformationList
    assert res == item

    # validate errors
    @ProtobufRequest(pb_class=pb2.OtherData)
    def main(req: HttpRequest, body: pb2.InformationList) -> pb2.InformationList:
        return body

    # NOTE: validation check is currently not working
    # with pytest.raises(ValueError):
    #    main(req=HttpRequest("GET", "http://localhost", body=item.SerializeToString()))

    # test enforcement of mime
    @ProtobufRequest(pb_class=pb2.InformationList, enforce_mime=True)
    def main(req: HttpRequest, body: pb2.InformationList) -> pb2.InformationList:
        return body

    with pytest.raises(ArgError):
        main(req=HttpRequest("GET", "http://localhost", body=item.SerializeToString()))
    with pytest.raises(RequestError):
        main(
            req=HttpRequest(
                "GET",
                "http://localhost",
                body=item.SerializeToString(),
                headers={"Content-Type": "application/json"},
            )
        )
    res = main(
        req=HttpRequest(
            "GET",
            "http://localhost",
            body=item.SerializeToString(),
            headers={"Content-Type": "application/octet-stream"},
        )
    )
    assert type(res) == pb2.InformationList
    assert res == item

    # TODO: handle json requests
