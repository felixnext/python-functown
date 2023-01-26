"""
Helper Class to decode JWT Tokens and verify the claims.

Note: This is currently required for python functions as they have no claim principal

Copyright 2022 - Felix Geilert
"""

import base64
from dataclasses import dataclass
import logging
from time import time
from typing import Dict, Any, Union, Set, List

import requests
from jose import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from functown.errors import TokenError


BEARER = "bearer "


@dataclass
class Token:
    """Token object that contains the claims of the token.

    Args:
        name (str): Passed username in the token
        oid (str): Unique ID of the user
        scopes (set): Set of access scopes for the user from the token
        local_mode (bool): Defines if function runs in local mode
    """

    user_id: str
    scopes: Set[str]
    verified: bool = False
    claims: Dict[str, Any] = None
    _local: bool = False

    @property
    def local(self) -> bool:
        """Returns if the function is running in local mode."""
        return self._local


def _ensure_bytes(key: Union[str, bytes]) -> bytes:
    """Make sure the key is bytes"""
    if isinstance(key, str):
        key = key.encode("utf-8")
    return key


def _decode_value(val):
    """Decodes a base64 encoded string."""
    decoded = base64.urlsafe_b64decode(_ensure_bytes(val) + b"==")
    return int.from_bytes(decoded, "big")


def decode_token(
    headers, issuer_url: str = None, audience: str = None, verify=True
) -> Token:
    """Verifies the request headers and returns a list of claims.

    Note that this will not verify the token as this should be done by azure.
    This also requires that the JWT token contains at least the following claims:
    - `oid`: The unique ID of the user
    - `scp`: The access scopes of the user
    - `exp`: The expiration time of the token

    Args:
        headers: req.header information to retrieve the token
        issuer_url (str): The issuer url to retrieve the public key. Only required if
            `verify` is set to `True`.
        audience (str): The audience to verify the token against. Only required if
            `verify` is set to `True`.
        verify (bool): Whether to verify the token signature against the issuer.
            Defaults to `True`.

    Returns:
        name (str): Passed username in the token
        oid (str): Unique ID of the user
        scopes (set): Set of access scopes for the user from the token
        local_mode (bool): Defines if function runs in local mode

    Raises:
        TokenError: If the token could not be parsed (this is a user facing error)
        ValueError: If the issuer url is not provided
        IOError: If the issuer data could not be retrieved
    """
    # get token
    hdict = dict(headers)
    token = hdict.get("authorization", None)
    min_len = len(BEARER)

    # validate if the token exists
    if token and len(token) > min_len:
        token = token[min_len:]
    else:
        raise TokenError("JWT Token could not be parsed")

    # check if in localmode (for azure functions)
    host = hdict.get("host", None)
    local_mode = host and host.split(":")[0].lower() == "localhost"

    # check if token should be verified
    if verify:
        # check if issuer url is provided
        if issuer_url is None:
            raise ValueError("Issuer URL is required for verification")
        if audience is None:
            logging.warning("Audience is not provided for verification")

        # parse headers from the JWT token
        header_data = jwt.get_unverified_header(token)

        # retrieve issuer data
        issuer_res = requests.request("get", issuer_url)
        if issuer_res.status_code != 200:
            raise IOError(f"Unable to obtain issuer data from {issuer_url}")
        issuer = issuer_res.json()

        # retrieve keys
        key_res = requests.request("get", issuer["jwks_uri"])
        if key_res.status_code != 200:
            raise IOError("Unable to obtain issuer key data")
        keys = key_res.json()

        # verify that kid matches
        sig = None
        for key in keys["keys"]:
            if header_data["kid"] == key["kid"]:
                sig = key
                break
        if not sig:
            raise TokenError("Token signature does not match")

        # retrieve pub key
        pk = (
            RSAPublicNumbers(n=_decode_value(sig["n"]), e=_decode_value(sig["e"]))
            .public_key(default_backend())
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

        # retrieve the algo from the header and decode
        claims = jwt.decode(
            token,
            key=pk,
            algorithms=[header_data["alg"]],
            audience=audience,
            issuer=issuer["issuer"],
        )
    else:
        logging.warning("JWT token is not verified!")
        claims = jwt.get_unverified_claims(token)

    # verify the claims
    if not local_mode:
        # retrieve azure passed data
        user_id = hdict.get("x-ms-client-principal-id", None)
        user_name = hdict.get("x-ms-client-principal-name", None)

        # compare
        if (user_id and user_id != claims["oid"]) or (
            user_name and user_name != claims.get("name", user_name)
        ):
            raise TokenError("Provided user information does not match")
    else:
        logging.info("Executing local mode (avoid user check)")

    # verify if token is expired
    cur_time = time()
    if claims["exp"] < cur_time:
        logging.error(
            f"Current time is {cur_time} but token is expired at {claims['exp']} "
            f"(diff: {claims['exp'] - cur_time})"
        )
        raise TokenError("Token is expired")

    # further parse the claims
    scopes = set(claims["scp"].split(" "))

    # pass on the data
    return Token(claims["oid"], scopes, verify, claims, local_mode)


def verify_user(
    req,
    scopes: List[str] = None,
    issuer_url: str = None,
    audience: str = None,
    verify: bool = False,
) -> Token:
    """Verifies the user send in the request

    Args:
        req: HttpRequest that should be verified
        scopes: List of Scopes (strings) or single scope
        verify: Defines if the JWT token should be verified with the provider

    Returns:
        user: User name in the Token
        user_id: User Id in the token
        scopes: Scopes from the token
        local: If the request was send from localhost
    """
    # verify the token
    try:
        token = decode_token(req.headers, issuer_url, audience, verify=verify)
    except TokenError as ex:
        raise TokenError(ex.msg, 500)

    # verify scopes
    if scopes:
        # make sure scopes are list
        if not isinstance(scopes, (list, tuple)):
            scopes = [scopes]

        # iterate scopes
        for scp in scopes:
            if scp not in token.scopes:
                raise TokenError("Missing authorization scope for current access", 401)

    # provide data
    return token
