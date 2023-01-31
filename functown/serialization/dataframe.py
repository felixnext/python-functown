"""Converts data from and to dataframes.

Supporting the following formats:
- CSV
- JSON
- Parquet

Copyright (c) 2023, Felix Geilert
"""

from enum import Enum
from io import StringIO, BytesIO
from typing import Dict, Tuple, Union, Optional

from azure.functions import HttpRequest
import pandas as pd

from functown.args import ContentTypes, RequestArgHandler, HeaderEnum
from functown.errors import RequestError

from .base import SerializationDecorator, DeserializationDecorator


class DataFrameFormat(str, Enum):
    """Supported DataFrame formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class DataFrameResponse(SerializationDecorator):
    """Provides a DataFrame serialized response for an Azure Function.

    Args:
        func (Callable): The function to decorate.
        format (DataFrameFormat): The format to use for serialization. Defaults to
            `DataFrameFormat.CSV`.
        headers (Dict[str, str]): The headers to add to the response.
        status_code (int): The status code of the response.
        allow_empty (bool): Whether to allow empty dataframes as input. Defaults to
            `True`.

    Example:
        >>> @DataFrameResponse
        ... def main(req: HttpRequest) -> pd.DataFrame:
        ...     return pd.DataFrame(...)
    """

    def __init__(
        self,
        func=None,
        format=DataFrameFormat.CSV,
        headers: Optional[Dict[str, str]] = None,
        status_code: int = 200,
        allow_empty: bool = True,
        **kwargs,
    ):
        super().__init__(func, headers, status_code, **kwargs)

        self._format = format
        self._allow_empty = allow_empty

    def serialize(
        self, req: HttpRequest, res: pd.DataFrame, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        # check if dataframe is valid
        if not isinstance(res, pd.DataFrame):
            raise ValueError(f"Response is not a valid DataFrame (is {type(res)})")
        if self._allow_empty is False and (res is None or res.empty):
            raise ValueError("Response is empty")
        is_empty = res is None or res.empty

        # serialize dataframe according to format
        if self._format == DataFrameFormat.CSV:
            data = res.to_csv(index=False) if not is_empty else None
            mime = ContentTypes.CSV
        elif self._format == DataFrameFormat.JSON:
            data = res.to_json(orient="records") if not is_empty else None
            mime = ContentTypes.JSON
        elif self._format == DataFrameFormat.PARQUET:
            data = res.to_parquet() if not is_empty else None
            mime = ContentTypes.BINARY
        else:
            raise ValueError(f"Unsupported DataFrame format: {self._format}")

        return data, mime


class DataFrameRequest(DeserializationDecorator):
    """Provides a DataFrame deserialized request for an Azure Function.

    This decorator will add a `df` keyword argument to the decorated function. This
    argument will contain the deserialized DataFrame.

    Args:
        func (Callable): The function to decorate.
        fixed_format (DataFrameFormat): The format to use for deserialization. If
            `None`, the format will be determined from the `Content-Type` header.
            Defaults to `None`.
        enforce_mime (bool): Whether to enforce the `Content-Type` header to match
            the format. Defaults to `False`.
    """

    def __init__(
        self,
        func=None,
        fixed_format: Optional[DataFrameFormat] = None,
        enforce_mime: bool = False,
        **kwargs,
    ):
        super().__init__(func, keyword="df", **kwargs)

        self._fixed_format = fixed_format
        self._enforce = enforce_mime
        self._fixed_mime = {
            DataFrameFormat.CSV: ContentTypes.CSV,
            DataFrameFormat.JSON: ContentTypes.JSON,
            DataFrameFormat.PARQUET: ContentTypes.BINARY,
        }.get(fixed_format, None)

    def deserialize(self, req: HttpRequest, *args, **kwargs) -> pd.DataFrame:
        # validate mime type
        mime = RequestArgHandler(req).get_header(
            HeaderEnum.CONTENT_TYPE, required=self._enforce
        )
        mime = mime.split(";")[0].lower() if mime is not None else None

        # check for hard request
        if self._fixed_mime is not None and mime != self._fixed_mime.value.lower():
            raise RequestError(
                f"Request body must be {self._fixed_mime.value} (is {mime}).", 400
            )
        if self._enforce is True and mime is None:
            raise RequestError("Request body must have a Content-Type header.", 400)

        # normalize body
        body = req.get_body()
        if body is None:
            return None
        # NOTE: using lambdas for lazy evaluation
        if isinstance(body, str):
            body_str, body_bytes = lambda: body, lambda: body.encode("utf-8")
        elif isinstance(body, bytes):
            body_str, body_bytes = lambda: body.decode("utf-8"), lambda: body
        else:
            raise RequestError(f"Unsupported body type: {type(body)}", 400)

        # parse dataframe
        if mime == ContentTypes.CSV.value.lower():
            df = pd.read_csv(StringIO(body_str()))
        elif mime == ContentTypes.JSON.value.lower():
            df = pd.read_json(StringIO(body_str()))
        elif mime == ContentTypes.BINARY.value.lower():
            df = pd.read_parquet(BytesIO(body_bytes()))
        else:
            raise RequestError(f"Unsupported content type: {mime}", 400)

        return df
