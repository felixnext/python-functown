"""Decorator to automatically parse request items from the Azure function.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest

from functown.utils import BaseDecorator
from .handler import RequestArgHandler


class ArgsHandler(BaseDecorator):
    """Decorator to automatically parse HttpRequest parameters.

    This will add an `args` parameter of type `RequestArgHandler` to the inner function
    signature.
    """

    def __init__(self, **kwargs):
        super().__init__(None, added_kw=["args"], **kwargs)

    def run(self, func, *args, **kwargs):
        req: HttpRequest = self._get("req", 0, *args, **kwargs)
        reqhandler = RequestArgHandler(req)
        kwargs["args"] = reqhandler

        return func(*args, **kwargs)
