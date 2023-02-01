"""
Bunch of Handler Code for Arguments

Copyright (c) 2023, Felix Geilert
"""


from distutils.util import strtobool
from enum import Enum
import logging
from typing import Any, Optional, Union, List, Callable

from azure.functions import HttpRequest

from functown.errors import ArgError


# create enum str class with different header names
class HeaderEnum(str, Enum):
    """List of Headers to be used in typed way"""

    AUTHORIZATION = "Authorization"
    CONTENT_TYPE = "Content-Type"
    ACCEPT = "Accept"
    HOST = "Host"
    USER_AGENT = "User-Agent"
    X_FORWARDED_FOR = "X-Forwarded-For"
    X_FORWARDED_PROTO = "X-Forwarded-Proto"
    X_FORWARDED_HOST = "X-Forwarded-Host"
    X_FORWARDED_PORT = "X-Forwarded-Port"
    X_FORWARDED_PREFIX = "X-Forwarded-Prefix"
    X_FORWARDED_PATH = "X-Forwarded-Path"
    X_FORWARDED_QUERY = "X-Forwarded-Query"
    X_FORWARDED_METHOD = "X-Forwarded-Method"
    X_FORWARDED_SCHEME = "X-Forwarded-Scheme"
    X_FORWARDED_PROTOCOL = "X-Forwarded-Protocol"
    X_FORWARDED_URI = "X-Forwarded-Uri"
    X_FORWARDED_URL = "X-Forwarded-Url"


class ContentTypes(str, Enum):
    """List of Content Types to be used in typed way"""

    JSON = "application/json"
    XML = "application/xml"
    PARQUET = "application/parquet"
    CSV = "text/csv"
    HTML = "text/html"
    TEXT = "text/plain"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    BINARY = "application/octet-stream"


class RequestArgHandler:
    def __init__(self, req: HttpRequest):
        self.req = req

        # create a header-map
        if req is None:
            logging.warning("Request is None, no data will be available")
            self._headers = {}
        else:
            headers = list(req.headers.keys())
            self._headers = dict(zip([h.lower() for h in headers], headers))

    def _convert(
        self,
        name: str,
        arg: str,
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[Any, List[Any]]]:
        # check if required
        if required and arg is None:
            raise ArgError(f"Argument {name} is not set, but required!", 400)

        # execute the mapping function (if set and arg is present)
        if map_fct is not None and arg is not None:
            if isinstance(map_fct, str):
                if map_fct == "bool":
                    if not isinstance(arg, bool):
                        arg = bool(strtobool(str(arg)))
                else:
                    arg = getattr(arg, map_fct)()
            else:
                arg = map_fct(arg)

        # check for default
        if arg is None and default is not None:
            arg = default

        # checks if in list
        if allowed and arg:
            # check for mapping
            if list_map and isinstance(list_map, str):
                ls_arg = getattr(arg, list_map)()
            else:
                ls_arg = list_map(arg) if list_map else arg

            # check if value found
            if ls_arg not in allowed:
                raise ArgError(
                    f"Argument {name} should be one of {allowed} but got {arg}", 400
                )

        return arg

    def _parse_body(self, name: str) -> Optional[Any]:
        arg = None
        try:
            body = self.req.get_json()
            arg = body[name] if name in body else None
        except Exception:
            logging.warning("Could not parse request body to json")
        return arg

    def get_body(
        self,
        name,
        required=False,
        map_fct=None,
        allowed=None,
        list_map=None,
        default=None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        """Parses a value from the body of the request

        Args:
            name (str): Name of the argument
            required (bool, optional): If the argument is required. Defaults to False.
            map_fct (function, optional): Function to map the value. Defaults to None.
            allowed (list, optional): List of allowed values. Defaults to None.
            list_map (function, optional): Function to map the list. Defaults to None.
            default (any, optional): Default value if not set. Defaults to None.
        """
        arg = self._parse_body(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_query(
        self,
        name: str,
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        """Parses a value from the query string of the request"""
        arg = self.req.params.get(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_route(
        self,
        name: str,
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        """Parses a value from the route parameters of the request"""
        arg = self.req.route_params.get(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_body_query(
        self,
        name: str,
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        """Parses a value from the body or query string of the request"""
        arg = self.req.params.get(name)
        if not arg and self.req.get_body():
            arg = self._parse_body(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_form(
        self,
        name: str,
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        arg = None
        try:
            arg = self.req.form[name]
        except Exception as ex:
            logging.warning(f"Form value {name} could not be parsed: {ex}")
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_file(self, name: str, required: bool = False) -> Optional[Any]:
        """Parses a file from the form data of the request"""
        file = None

        # retrieve data
        try:
            file = self.req.files[name]
        except Exception as ex:
            logging.warning(f"File {name} could not be parsed: {ex}", 400)

        # check if provided
        if required and not file:
            raise ArgError(f"File {name} could not be parsed", 400)

        return file

    def get_header(
        self,
        name: Union[str, HeaderEnum],
        required: bool = False,
        map_fct: Callable[[str], Any] = None,
        allowed: Optional[List[Any]] = None,
        list_map: Callable[[Any], List[Any]] = None,
        default: Optional[Any] = None,
    ) -> Optional[Union[str, Any, List[Any]]]:
        """Parses a header from the request

        Note: You can use `HeaderEnum` to get the correct header name
        """
        # preprocess name
        if isinstance(name, HeaderEnum):
            name = name.value
        name = self._headers.get(name.lower(), name)

        # check if provided
        arg = self.req.headers.get(name)

        if arg is None:
            if required:
                raise ArgError(f"Header {name} is required", 400)
            return None
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)
