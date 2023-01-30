"""Converts data from and to dataframes.

Supporting the following formats:
- CSV
- JSON
- Parquet

Copyright (c) 2023, Felix Geilert
"""

from typing import Any, Dict, Tuple, Union

from azure.functions import HttpRequest

# import pandas as pd

# from functown.args import ContentTypes, RequestArgHandler, HeaderEnum
# from functown.errors import RequestError

from .base import SerializationDecorator, DeserializationDecorator


class DataFrameResponse(SerializationDecorator):
    """Provides a DataFrame serialized response for an Azure Function."""

    def __init__(
        self,
        func=None,
        headers: Dict[str, str] = None,
        status_code: int = 200,
        **kwargs
    ):
        super().__init__(func, headers, status_code, **kwargs)

    def serialize(
        self, req: HttpRequest, res: Any, *args, **kwargs
    ) -> Tuple[Union[bytes, str], str]:
        pass


class DataFrameRequest(DeserializationDecorator):
    """Provides a DataFrame deserialized request for an Azure Function."""

    def __init__(self, func=None, **kwargs):
        super().__init__(func, keyword="df", **kwargs)

    def deserialize(self, req: HttpRequest, *args, **kwargs) -> Any:
        pass
