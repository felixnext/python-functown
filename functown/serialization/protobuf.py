"""Parsing of protobuf messages.

Copyright (c) 2023, Felix Geilert
"""

from typing import Any, Dict, Tuple, Union

from azure.functions import HttpRequest
from functown.args import RequestArgHandler, HeaderEnum, ContentTypes
from functown.errors import RequestError
from google.protobuf import json_format

from .base import SerializationDecorator, DeserializationDecorator


class ProtobufResponse(SerializationDecorator):
    """Provides a protobuf serialized response for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        pb_class (Any): The protobuf class to use for serialization. If provided, will
            perform a hard type check on the response. Defaults to `None`.
        headers (Dict[str, str]): The headers to add to the response.
        status_code (int): The status code of the response.
        allow_json (bool): Whether to allow dict or list objects as input. In this case
            the object will automatically be converted into the regarding protobuf
            class. (Note that this strictly requires pb_class to be provided).
            Defaults to `None` (True if pb_class provided).

    Example:
        >>> @ProtobufResponse
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     pb = pb2.Example()
        ...     return pb

        >>> @ProtobufResponse(headers={"X-My-Header": "My-Value"})
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     pb = pb2.Example()
        ...     return pb
    """

    def __init__(
        self,
        func=None,
        pb_class: Any = None,
        headers: Dict[str, str] = None,
        status_code: int = 200,
        allow_json: bool = None,
        **kwargs,
    ):
        super().__init__(func, headers, status_code, **kwargs)
        self._pb_class = pb_class
        self._allow_json = (
            allow_json if allow_json is not None else pb_class is not None
        )

    def serialize(
        self, req: HttpRequest, res: Any, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        # check if already serialized
        if isinstance(res, bytes):
            return res, ContentTypes.BINARY

        # perform type check (if requested)
        if self._pb_class is not None:
            # check if json or list and convert
            if self._allow_json is True and isinstance(res, (list, dict)):
                res = json_format.ParseDict(res, self._pb_class())
            elif not isinstance(res, self._pb_class):
                raise ValueError(f"Response is not of type {self._pb_class.__name__}")

        # check for SerializeToString method
        if not hasattr(res, "SerializeToString"):
            raise ValueError("Response does not have a SerializeToString method")

        return res.SerializeToString(), ContentTypes.BINARY


class ProtobufRequest(DeserializationDecorator):
    """Provides a Protobuf deserialized request for an Azure Function.

    This decorator will add a `body` argument to the decorated function. This argument
    will contain the deserialized protobuf object.

    Args:
        func (Callable): The function to decorate.
        pb_class (Any): The protobuf class to use for deserialization.
        enfore_mime (bool): Whether to enforce the mimetype check of the request body.
            Defaults to `True`.
        allow_json (bool): Whether to allow JSON requests. This will automatically parse
            a JSON request into the regarding protobuf object. Defaults to `False`.

    Example:
        >>> @ProtoRequest()
        ... def main(req: HttpRequest, body: Any):
        ...     item = body.item
    """

    def __init__(
        self,
        pb_class: Any,
        enforce_mime: bool = True,
        allow_json: bool = True,
        **kwargs,
    ):
        super().__init__(None, **kwargs)

        # check if ParseFromString method exists
        if not hasattr(pb_class, "ParseFromString"):
            raise ValueError("Provided class does not have a ParseFromString method")

        # set data
        self._enforce = enforce_mime
        self._pb_class = pb_class
        self._allow_json = allow_json

    def deserialize(self, req: HttpRequest, *args, **kwargs) -> Any:
        # validate mimetype
        mime = RequestArgHandler(req).get_header(
            HeaderEnum.CONTENT_TYPE, required=self._enforce
        )
        mime = mime.split(";")[0].lower() if mime is not None else None

        # check for json data
        if mime == ContentTypes.JSON.value.lower() and self._allow_json is True:
            body = req.get_body()
            if isinstance(body, str):
                body = body.encode("utf-8")
            pb_item = self._pb_class()
            json_format.Parse(body, pb_item)
            return pb_item

        # check for hard request
        if self._enforce is True and mime != ContentTypes.BINARY.value.lower():
            raise RequestError(f"Request body must be octet-stream (is {mime}).", 400)

        # retrieve body and decode to string
        body = req.get_body()
        if isinstance(body, str):
            body = body.encode("utf-8")
        elif not isinstance(body, bytes):
            raise RequestError("Request body must be a str or bytes object.", 400)

        # FEAT: enable deeper parsing check
        pb_item = self._pb_class()
        pb_item.ParseFromString(body)
        return pb_item
