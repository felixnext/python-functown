"""Convert Request and Response data using Flatbuffers.

Copyright (c) 2023, Felix Geilert
"""

from typing import Dict, Any, Tuple, Union

from azure.functions import HttpRequest
import flatbuffers  # noqa: F401
from functown.args import ContentTypes, RequestArgHandler, HeaderEnum
from functown.errors import RequestError

from .base import SerializationDecorator, DeserializationDecorator


class FlatbufferResponse(SerializationDecorator):
    """Provides a Flatbuffer serialized response for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        fb_class (Any): The flatbuffer class to use for serialization. If provided, will
            perform a hard type check on the response. Defaults to `None`.
        headers (Dict[str, str]): The headers to add to the response.
        status_code (int): The status code of the response.
        allow_json (bool): Whether to allow dict or list objects as input. In this case
            the object will automatically be converted into the regarding flatbuffer
            class. (Note that this strictly requires fb_class to be provided).
            Defaults to `None` (True if fb_class provided).

    Example:
        >>> @FlatbufferResponse
        ... def main(req: HttpRequest) -> fb.Example:
        ...     fb = fb2.Example()
        ...     return fb
    """

    def __init__(
        self,
        func=None,
        fb_class: Any = None,
        headers: Dict[str, str] = None,
        status_code: int = 200,
        allow_json: bool = False,
        **kwargs,
    ):
        super().__init__(func, headers, status_code, **kwargs)
        self._fb_class = fb_class
        self._allow_json = (
            allow_json if allow_json is not None else fb_class is not None
        )

    def serialize(
        self, req: HttpRequest, res: Any, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        # check if already serialized
        if isinstance(res, bytes):
            return res, ContentTypes.binary

        # perform type check (if requested)
        if self._fb_class is not None:
            # check if json or list and convert
            if self._allow_json is True and isinstance(res, (list, dict)):
                # FIXME: convert
                raise NotImplementedError("JSON conversion not implemented yet")
            elif not isinstance(res, self._fb_class):
                raise ValueError(f"Response is not of type {self._fb_class.__name__}")

        # check for SerializeToString method
        if not hasattr(res, "Output"):
            raise ValueError("Response does not have a Output method")

        return bytes(res.Output()), "application/octet-stream"


class FlatbufferRequest(DeserializationDecorator):
    """Provides a Flatbuffer deserialized request for an Azure Function.

    Args:
        fb_class (Any): The flatbuffer class to use for deserialization.
        enfore_mime (bool): Whether to enforce the mimetype check of the request body.
            Defaults to `True`.
        allow_json (bool): Whether to allow JSON requests. This will automatically parse
            a JSON request into the regarding flatbuffer object. Defaults to `False`.

    Example:
        >>> @FlatbufferRequest()
        >>> def func(req: HttpRequest, data: fb.Example) -> Any:
        >>>     # do something with data
        >>>     return ...
    """

    def __init__(
        self,
        fb_class: Any,
        enforce_mime: bool = True,
        allow_json: bool = True,
        **kwargs,
    ):
        super().__init__(None, **kwargs)

        self._fb_class = fb_class
        self._enforce_mime = enforce_mime
        self._allow_json = allow_json

        if self._fb_class is None:
            raise ValueError("fb_class must be set")
        if not hasattr(self._fb_class, "GetRootAs"):
            raise ValueError("fb_class must have a GetRootAs method")

    def deserialize(self, req: HttpRequest, *args, **kwargs) -> Any:
        # validate mimetype
        mime = RequestArgHandler(req).get_header(
            HeaderEnum.content_type, required=self._enforce
        )
        mime = mime.split(";")[0].lower() if mime is not None else None

        # check for json data
        if mime == ContentTypes.json.value.lower() and self._allow_json is True:
            body = req.get_body()
            if isinstance(body, str):
                body = body.encode("utf-8")
            # FIXME: implement
            raise NotImplementedError("JSON conversion not implemented yet")

        # check for hard request
        if self._enforce is True and mime != ContentTypes.binary.value.lower():
            raise RequestError(f"Request body must be octet-stream (is {mime}).", 400)

        # retrieve body and decode to string
        body = req.get_body()
        if isinstance(body, str):
            body = body.encode("utf-8")
        elif not isinstance(body, bytes):
            raise RequestError("Request body must be a str or bytes object.", 400)

        # FIXME: generate the response object
