from distutils.util import strtobool
import json

import pytest
from azure.functions import HttpRequest

from functown import RequestArgHandler
from functown.errors import ArgError


def test_arghandler_convert():
    """Test the Parameter Conversion Methods to ensure they work properly"""
    args = RequestArgHandler(None)

    # direct pass through
    out = args._convert("foo", "baz", required=True)
    assert out == "baz"
    out = args._convert("foo", "baz", required=True, map_fct=lambda x: x.upper())
    assert out == "BAZ"
    out = args._convert("foo", "baz", required=True, map_fct="upper")
    assert out == "BAZ"
    out = args._convert("foo", None, map_fct="upper")
    assert out is None

    # check default
    out = args._convert("foo", None, default="baz")
    assert out == "baz"

    # bool conversion
    out = args._convert(
        "foo", "true", required=True, map_fct=lambda x: bool(strtobool(x))
    )
    assert out is True
    out = args._convert(
        "foo", "false", required=True, map_fct=lambda x: bool(strtobool(x))
    )
    assert out is False
    out = args._convert("foo", "false", required=True, map_fct="bool")
    assert out is False
    out = args._convert("foo", "true", required=True, map_fct="bool")
    assert out is True
    out = args._convert("foo", True, required=True, map_fct="bool")
    assert out is True
    out = args._convert("foo", False, required=True, map_fct="bool")
    assert out is False
    out = args._convert("foo", None, required=False, map_fct="bool", default=True)
    assert out is True
    out = args._convert("foo", None, required=False, map_fct="bool", default=False)
    assert out is False

    # int conversion
    out = args._convert("foo", "1", required=True, map_fct=int)
    assert out == 1
    out = args._convert("foo", "-100", required=True, map_fct=int)
    assert out == -100
    out = args._convert("foo", 1, required=True, map_fct=int)
    assert out == 1
    out = args._convert("foo", -99, required=True, map_fct=int)
    assert out == -99
    out = args._convert("foo", None, required=False, map_fct=int, default=1)
    assert out == 1
    out = args._convert("foo", None, required=False, map_fct=int, default=99)
    assert out == 99

    # check allowed values
    out = args._convert("foo", "bar", allowed=["foo", "bar", "baz"])
    assert out == "bar"
    out = args._convert("foo", "bar", allowed=["FOO", "BAR", "BAZ"], list_map="upper")
    assert out == "bar"
    out = args._convert("foo", "bar", allowed=["FOO", "BAR", "BAZ"], map_fct="upper")
    assert out == "BAR"
    out = args._convert("foo", None, allowed=["FOO", "BAR", "BAZ"], map_fct="upper")
    assert out is None

    # check default convert
    out = args._convert("foo", None, default=True, map_fct=strtobool)
    assert out is True

    # test error cases
    with pytest.raises(ArgError):
        out = args._convert("foo", None, required=True)

    with pytest.raises(ArgError):
        out = args._convert("foo", "bar", allowed=["foo", "baz"])


def test_arghandler_params():
    """Ensure that we can parse arguments from url query params"""
    req = HttpRequest(
        "GET", "foo/bar", params={"foo": "1", "bar": "true", "baz": "opt1"}, body=None
    )
    args = RequestArgHandler(req)

    # handle requests
    out = args.get_query("foo")
    assert out == "1"
    out = args.get_query("foo", map_fct=int)
    assert out == 1

    out = args.get_query("bar", map_fct="bool")
    assert out is True

    out = args.get_query("baz")
    assert out == "opt1"
    out = args.get_query("baz", allowed=["opt1", "opt2"])
    assert out == "opt1"
    with pytest.raises(ArgError):
        out = args.get_query("baz", allowed=["opt3", "opt2"])

    out = args.get_query("not_there")
    assert out is None
    out = args.get_query("not_there", default=True)
    assert out is True


def test_arghandler_body():
    """Ensure that we can parse arguments from request body"""
    req = HttpRequest(
        "GET",
        "foo/bar",
        body=json.dumps({"foo": "1", "bar": "true", "baz": "opt1"}).encode("utf-8"),
    )
    args = RequestArgHandler(req)

    # handle requests
    out = args.get_body("foo")
    assert out == "1"
    out = args.get_body("foo", map_fct=int)
    assert out == 1

    out = args.get_body("bar", map_fct="bool")
    assert out is True

    out = args.get_body("baz")
    assert out == "opt1"
    out = args.get_body("baz", allowed=["opt1", "opt2"])
    assert out == "opt1"
    with pytest.raises(ArgError):
        out = args.get_body("baz", allowed=["opt3", "opt2"])

    out = args.get_body("not_there")
    assert out is None
    out = args.get_body("not_there", default=True)
    assert out is True


def test_arghandler_querybody():
    """Ensure that we can parse arguments in combined fashion"""
    # split parameters and test all extrems
    req3 = HttpRequest(
        "GET",
        "foo/bar",
        params={"foo": "1", "bar": "true"},
        body=json.dumps({"baz": "opt1"}).encode("utf-8"),
    )
    req2 = HttpRequest(
        "GET",
        "foo/bar",
        body=json.dumps({"foo": "1", "bar": "true", "baz": "opt1"}).encode("utf-8"),
    )
    req1 = HttpRequest(
        "GET", "foo/bar", params={"foo": "1", "bar": "true", "baz": "opt1"}, body=None
    )

    # iterate through different request types
    for req in [req1, req2, req3]:
        args = RequestArgHandler(req)

        # handle requests
        out = args.get_body_query("foo")
        assert out == "1"
        out = args.get_body_query("foo", map_fct=int)
        assert out == 1

        out = args.get_body_query("bar", map_fct="bool")
        assert out is True

        out = args.get_body_query("baz")
        assert out == "opt1"
        out = args.get_body_query("baz", allowed=["opt1", "opt2"])
        assert out == "opt1"
        with pytest.raises(ArgError):
            out = args.get_body_query("baz", allowed=["opt3", "opt2"])

        out = args.get_body_query("not_there")
        assert out is None
        out = args.get_body_query("not_there", default=True)
        assert out is True


def test_arghandler_route():
    """Ensure that we can parse arguments from request body"""
    req = HttpRequest("GET", "foo/bar", route_params={"area": "foo"}, body=None)
    args = RequestArgHandler(req)

    # handle requests
    out = args.get_route("area")
    assert out == "foo"
    out = args.get_route("area", required=True)
    assert out == "foo"
    out = args.get_route("area", required=True, allowed=["foo", "bar"])
    assert out == "foo"

    out = args.get_route("section", default="bar")
    assert out == "bar"

    with pytest.raises(ArgError):
        out = args.get_route("area", allowed=["bar", "baz"])

    out = args.get_route("not_there")
    assert out is None
    out = args.get_route("not_there", default=True)
    assert out is True
