"""Decorator to automatically parse JWT Tokens from the request of the azure function.

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import List, Optional

from azure.functions import HttpRequest

from functown.utils import BaseDecorator
from functown.errors import TokenError
from .jwt import verify_user


class AuthHandler(BaseDecorator):
    """Decorator to automatically parse a JWT Token from the HttpRequest parameters.

    This will add an `token` parameter of type `Token` to the inner function signature.

    Args:
        scopes (list): List of scopes that are required for the token
        issuer_url (str): URL of the issuer of the token
        audience (str): Audience of the token
        verify (bool): Whether to verify the token signature against the issuer.
            Defaults to `True`.
        auto_disable_verify (bool): Whether to automatically disable token verification
            if no issuer_url is provided. Defaults to `True`.
        debug (bool): Whether to provide addditional info in error messages for
            debugging. Defaults to `False`.
    """

    def __init__(
        self,
        scopes: Optional[List[str]] = None,
        issuer_url: Optional[str] = None,
        audience: Optional[str] = None,
        verify: bool = True,
        auto_disable_verify: bool = True,
        debug: bool = False,
        **kwargs,
    ):
        super().__init__(None, added_kw=["token"], **kwargs)

        self.scopes = scopes
        self.issuer_url = issuer_url
        self.audience = audience
        if verify and not issuer_url:
            if auto_disable_verify:
                logging.warning(
                    "No issuer_url provided, but verify is True. "
                    "Disabling token verification."
                )
                verify = False
            else:
                raise ValueError("No issuer_url provided, but verify is True.")
        self.verify = verify
        self.debug = debug

    def run(self, func, *args, **kwargs):
        # retrieve request
        req: HttpRequest = self._get("req", 0, *args, **kwargs)

        # get logger
        logger = self._get("logger", None, *args, **kwargs) or logging

        # parse token
        try:
            token = verify_user(
                req,
                scopes=self.scopes,
                issuer_url=self.issuer_url,
                audience=self.audience,
                verify=self.verify,
                logger=logger,
            )
        except TokenError as ex:
            if self.debug:
                raise ex
            raise TokenError("Token validation failed", 401)
        except Exception as ex:
            msg = "Internal error during verification"
            if self.debug:
                msg += f": {ex}"
            raise TokenError(msg, 500)

        kwargs["token"] = token

        return func(*args, **kwargs)
