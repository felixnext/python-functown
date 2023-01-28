"""Provides Serialization and Deserialization Decorator objects.

Copyright (c) 2023, Felix Geilert
"""

from abc import abstractmethod
from typing import Any, Dict, Tuple, Union

from azure.functions import HttpResponse, HttpRequest

from functown.utils import BaseDecorator


class SerializationDecorator(BaseDecorator):
    """Provides a serialized response for an Azure Function.

    Derived classes should implement the `serialize` method, which retrieves the
    result of inner function execution as well as remaining function parameters
    (including the request).

    Args:
    """

    def __init__(
        self,
        func=None,
        headers: Dict[str, str] = None,
        status_code: int = 200,
        **kwargs
    ):
        super().__init__(func, **kwargs)

        self._headers = headers
        self._code = status_code

    @abstractmethod
    def serialize(
        self, req: HttpRequest, res: Any, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        """Serializes the result of the function.

        Args:
            req (HttpRequest): The request object.
            res (Any): The result of the function.

        Returns:
            data (bytes | str): The serialized result.
            mime (str): The mimetype of the serialized result.
        """
        raise NotImplementedError

    def run(self, func, *args, **kwargs):
        # execute inner function
        res = func(*args, **kwargs)

        # get request object
        req = self._get("req", 0, *args, **kwargs)
        if "req" in kwargs:
            del kwargs["req"]
        else:
            args = args[1:]

        # serialize result
        data, mtype = self.serialize(req, res, *args, **kwargs)
        return HttpResponse(
            data, status_code=self._code, headers=self._headers, mimetype=mtype
        )


class DeserializationDecorator(BaseDecorator):
    """Provides a deserialized request body for an Azure Function.

    This will add a `body` parameter to the function signature, which contains the
    deserialized request body.
    """

    def __init__(self, func=None, **kwargs):
        super().__init__(func, ["body"], **kwargs)

    @abstractmethod
    def deserialize(self, req: HttpRequest, *args, **kwargs) -> Any:
        """Deserializes the request body.

        Args:
            req (HttpRequest): The request object.

        Returns:
            data (Any): The deserialized request body.
        """
        raise NotImplementedError

    def run(self, func, *args, **kwargs):
        # retrieve the request
        req = self._get("req", 0, *args, **kwargs)
        if "req" in kwargs:
            del kwargs["req"]
        else:
            args = args[1:]

        # deserialize request body
        body = self.deserialize(req, *args, **kwargs)
        kwargs["body"] = body

        # execute inner function
        return func(req=req, *args, **kwargs)
