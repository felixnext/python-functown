"""Converts input as either json or protobuf

Note: This does not include deserialize as Protobuf can handle that.

Copyright (c) 2023, Felix Geilert
"""

import typing as tp
import logging
import json

from azure.functions import HttpRequest

from functown.args import ContentTypes, RequestArgHandler, HeaderEnum
from google.protobuf import json_format

from .base import SerializationDecorator


class HybridProtoResponse(SerializationDecorator):
    """Provides a protobuf serialized response for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        pb_class (Any): The protobuf class to use for serialization. If
            provided, will perform a hard type check on the response.
            Defaults to `None`.
        headers (Dict[str, str]): The headers to add to the response.
        status_code (int): The status code of the response.
        allow_json (bool): Whether to allow dict or list objects as input. In
            this case the object will automatically be converted into the
            regarding protobuf class. (Note that this strictly requires pb_class
            to be provided). Defaults to `None` (True if pb_class provided).
        json_all_fields (bool): Whether to include all fields in the JSON
            response. Defaults to `True`.

    Example:
        >>> @HybridResponse
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     pb = pb2.Example()
        ...     return pb

        >>> @HybridResponse(headers={"X-My-Header": "My-Value"})
        ... def main(req: HttpRequest) -> Dict[str, str]:
        ...     pb = pb2.Example()
        ...     return pb
    """

    def __init__(
        self,
        func=None,
        pb_class: tp.Any = None,
        headers: tp.Optional[tp.Dict[str, str]] = None,
        status_code: int = 200,
        allow_json: tp.Optional[bool] = None,
        json_all_fields: bool = True,
        **kwargs,
    ):
        super().__init__(func, headers, status_code, **kwargs)
        self._pb_class = pb_class
        self._json_all = json_all_fields
        self._allow_json = (
            allow_json if allow_json is not None else pb_class is not None
        )

    def serialize(
        self, req: HttpRequest, res: tp.Any, *args, **kwargs
    ) -> tp.Tuple[tp.Union[bytes, str], str]:
        # check for request header
        mime_raw = RequestArgHandler(req).get_header(
            HeaderEnum.CONTENT_TYPE, required=False
        )
        mime = (
            mime_raw.split(";")[0].lower()
            if mime_raw is not None and isinstance(mime_raw, str)
            else None
        )

        # check for response type
        use_json = False
        if mime == ContentTypes.JSON.value.lower():
            use_json = True
        elif mime != ContentTypes.BINARY.value.lower():
            logging.warning(f"Unknown mime type '{mime}', defaulting to binary/json")

        # check if already serialized
        if isinstance(res, bytes):
            if use_json is False:
                return res, ContentTypes.BINARY
            # convert from serialized data to protobuf
            res = self._pb_class.FromString(res)

        # perform type check (if requested)
        if self._pb_class is not None:
            # check if json or list and convert
            if self._allow_json is True and isinstance(res, (list, dict)):
                res = json_format.ParseDict(res, self._pb_class())
            elif not isinstance(res, self._pb_class):
                raise ValueError(f"Response is not of type {self._pb_class.__name__}")
        elif (isinstance(res, dict) or isinstance(res, list)) and (
            use_json is True or mime != ContentTypes.BINARY.value.lower()
        ):
            # NOTE: return json if pb_class is not provided and not explicit
            # request as cast
            logging.warning("Auto-Casting to JSON response")
            return json.dumps(res), ContentTypes.JSON

        # check for SerializeToString method
        if not hasattr(res, "SerializeToString") and use_json is False:
            raise ValueError(
                f"Response ({type(res)}) does not have a " "SerializeToString method"
            )

        # execute correct response
        if use_json is True:
            # DEBT: sub-objects are skipped instead of null values
            # dict = json_format.MessageToDict(
            #     res,
            #     # NOTE: this is helpful for gql parsing
            #     # (avoid resolver errors)
            #     including_default_value_fields=self._json_all,
            #     # NOTE: ensure consistency between proto and gql schema
            #     preserving_proto_field_name=True,
            # )
            # iterate all fields in type and add missing null fields

            return (
                json_format.MessageToJson(
                    res,
                    # NOTE: this is helpful for gql parsing
                    # (avoid resolver errors)
                    including_default_value_fields=self._json_all,
                    # NOTE: ensure consistency between proto and gql schema
                    preserving_proto_field_name=True,
                ),
                ContentTypes.JSON,
            )
        return res.SerializeToString(), ContentTypes.BINARY
