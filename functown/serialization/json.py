"""Json Serialization Decorator.

Copyright (c) 2023, Felix Geilert
"""

import json
from typing import Any, Dict, Tuple, Union

from azure.functions import HttpRequest
from functown.args import RequestArgHandler, HeaderEnum
from functown.errors import RequestError

from .base import SerializationDecorator, DeserializationDecorator


class JsonResponse(SerializationDecorator):
    """Provides a JSON serialized response for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        headers (Dict[str, str]): The headers to add to the response.
        status_code (int): The status code of the response.

    Example:
        >>> @JsonResponse
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     return {"hello": "world"}

        >>> @JsonResponse(headers={"X-My-Header": "My-Value"})
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     return {"hello": "world"}
    """

    def __init__(
        self,
        func=None,
        headers: Dict[str, str] = None,
        status_code: int = 200,
        **kwargs,
    ):
        super().__init__(func, headers, status_code, **kwargs)

    def serialize(
        self, req: HttpRequest, res: Any, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        return json.dumps(res), "application/json"


class JsonRequest(DeserializationDecorator):
    """Provides a JSON deserialized request for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        enfore_mime (bool): Whether to enforce the mimetype check of the request body.
            Defaults to `True`.

    Example:
        >>> @JsonRequest
        ... def main(req: HttpRequest, body: dict):
        ...     item = body["item"]
    """

    def __init__(self, func=None, enfore_mime: bool = True, **kwargs):
        super().__init__(func, **kwargs)
        self._enforce = enfore_mime

    def deserialize(self, req: HttpRequest, *args, **kwargs) -> Any:
        # validate mimetype
        mime = RequestArgHandler(req).get_header(
            HeaderEnum.content_type, required=self._enforce
        )
        mime = mime.split(";")[0]
        if self._enforce is True and mime != "application/json":
            raise RequestError(f"Request body must be JSON (is {mime}).", 400)

        # retrieve body and decode to string
        body = req.get_body()
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        elif not isinstance(body, str):
            raise RequestError("Request body must be a string or bytes object.", 400)

        # handle loading
        return json.loads(body)
