"""Decorator to automatically parse JWT Tokens from the request of the azure function.

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import List, Optional

from azure.functions import HttpRequest

from functown.utils import BaseDecorator
from .jwt import verify_user


class AuthHandler(BaseDecorator):
    """Decorator to automatically parse a JWT Token from the HttpRequest parameters.

    This will add an `token` parameter of type `Token` to the inner function signature.
    """

    def __init__(
        self,
        scopes: Optional[List[str]] = None,
        issuer_url: Optional[str] = None,
        audience: Optional[str] = None,
        verify: bool = True,
        auto_disable_verify: bool = True,
        **kwargs
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

    def run(self, func, *args, **kwargs):
        # retrieve request
        req: HttpRequest = self._get("req", 0, *args, **kwargs)

        # parse token
        token = verify_user(
            req,
            scopes=self.scopes,
            issuer_url=self.issuer_url,
            audience=self.audience,
            verify=self.verify,
        )

        kwargs["token"] = token

        return func(*args, **kwargs)
