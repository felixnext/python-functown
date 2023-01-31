"""Tests the usage of Flatbuffer serialization.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest, HttpResponse
import flatbuffers
import pytest

from functown.errors import ArgError, RequestError
from functown.serialization import FlatbufferResponse, FlatbufferRequest
from .resources.functown.example import (
    SubInfo,
    InformationList,
    Importance,
    Information,
)


@pytest.fixture
def fb_data():
    # generate a flatbuffer (1024 = initial size)
    builder = flatbuffers.Builder(1024)
    infos = []
    for i in range(3):
        msg = builder.CreateString(f"Hello World {i}")
        SubInfo.Start(builder)
        SubInfo.AddMsg(builder, msg)
        SubInfo.AddType(builder, Importance.Importance().High)
        infos.append(SubInfo.End(builder))
    Information.StartDataVector(builder, 3)
    for i in reversed(infos):
        builder.PrependUOffsetTRelative(i)
    data = builder.EndVector(3)
    msg = builder.CreateString("Hello World")
    Information.Start(builder)
    Information.AddMsg(builder, msg)
    Information.AddId(builder, 1)
    Information.AddScore(builder, 0.5)
    Information.AddData(builder, data)
    info = Information.End(builder)

    InformationList.StartInfosVector(builder, 1)
    builder.PrependUOffsetTRelative(info)
    infos = builder.EndVector(1)
    InformationList.Start(builder)
    InformationList.AddInfos(builder, infos)
    item = InformationList.End(builder)
    builder.Finish(item)

    bt = bytes(builder.Output())
    assert type(bt) == bytes

    return bt, builder


def test_flatbuffer_response(fb_data):
    """Tests flatbuffer response serialization."""
    # retrieve data
    byte_data, builder = fb_data

    # test return of bytes
    @FlatbufferResponse
    def main(req: HttpRequest) -> InformationList:
        return byte_data

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert type(res) == HttpResponse
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == byte_data

    # test return of builder
    @FlatbufferResponse
    def main(req: HttpRequest) -> InformationList:
        return builder

    res = main(req=HttpRequest("GET", "http://localhost", body=None))
    assert type(res) == HttpResponse
    assert res.mimetype == "application/octet-stream"
    assert res.get_body() == byte_data


def test_flatbuffer_request(fb_data):
    # retrieve data
    byte_data, builder = fb_data

    # test return data object
    @FlatbufferRequest(InformationList.InformationList, enforce_mime=False)
    def main(
        req: HttpRequest, body: InformationList.InformationList
    ) -> InformationList.InformationList:
        return body

    # check regular type
    req = HttpRequest("GET", "http://localhost", body=byte_data)
    res = main(req=req)
    assert type(res) == InformationList.InformationList

    # validate mime types
    @FlatbufferRequest(InformationList.InformationList, enforce_mime=True)
    def main(
        req: HttpRequest, body: InformationList.InformationList
    ) -> InformationList.InformationList:
        return body

    # assert wrong and no mime type
    req = HttpRequest("GET", "http://localhost", body=byte_data)
    with pytest.raises(ArgError):
        main(req=req)

    req = HttpRequest(
        "GET",
        "http://localhost",
        body=byte_data,
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(RequestError):
        main(req=req)

    # assert correct mime type
    req = HttpRequest(
        "GET",
        "http://localhost",
        body=byte_data,
        headers={"Content-Type": "application/octet-stream"},
    )
    res = main(req=req)
    assert type(res) == InformationList.InformationList
