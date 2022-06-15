"""
Helper Class to decode JWT Tokens and verify the claims.

Note: This is currently required for python functions as they have no claim principal

Copyright 2022 - Felix Geilert
"""


import os
import logging
from time import time
import base64

import requests
from jose import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from functown.errors import TokenError


BEARER = "bearer "


def ensure_bytes(key):
    if isinstance(key, str):
        key = key.encode("utf-8")
    return key


def decode_value(val):
    decoded = base64.urlsafe_b64decode(ensure_bytes(val) + b"==")
    return int.from_bytes(decoded, "big")


def decode_token(headers, verify=True):
    """Verifies the request headers and returns a list of claims.

    Note that this will not verify the token as this should be done by azure.

    Args:
        headers: req.header information to retrieve the token

    Returns:
        name (str): Passed username in the token
        oid (str): Unique ID of the user
        scopes (set): Set of access scopes for the user from the token
        local_mode (bool): Defines if function runs in local mode
    """
    # get token
    hdict = dict(headers)
    token = hdict.get("authorization", None)
    if token and len(token) > len(BEARER):
        token = token[len(BEARER) :]
    else:
        raise TokenError("JWT Token could not be parsed")

    # check if in localmode
    host = hdict.get("host", None)
    local_mode = host and host.split(":")[0].lower() == "localhost"

    if verify:
        # retrieve the headers
        header_data = jwt.get_unverified_header(token)

        # retrieve issuer data
        issuer_res = requests.request("get", os.getenv("B2C_ISSUER_URL"))
        if issuer_res.status_code != 200:
            raise IOError("Unable to obtain issuer data")
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
            RSAPublicNumbers(n=decode_value(sig["n"]), e=decode_value(sig["e"]))
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
            audience=os.getenv("B2C_APP_ID"),
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
            user_name and user_name != claims["name"]
        ):
            raise TokenError("Provided user information does not match")
    else:
        logging.info("Executing local mode (avoid user check)")

    # verify if token is expired
    cur_time = time()
    if claims["exp"] < cur_time:
        logging.error(
            f"Current time is {cur_time} but token is expired at {claims['exp']} (diff: {claims['exp'] - cur_time})"
        )
        raise TokenError("Token is expired")

    # further parse the claims
    scopes = set(claims["scp"].split(" "))

    # pass on the data
    return claims["name"], claims["oid"], scopes, local_mode


def verify_user(req, scopes=None, verify=False):
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
        user, user_id, user_scp, local = decode_token(req.headers, verify=verify)
    except TokenError as ex:
        raise TokenError(ex.msg, 500)

    # verify scopes
    if scopes:
        # make sure scopes are list
        if not isinstance(scopes, (list, tuple)):
            scopes = [scopes]

        # iterate scopes
        for scp in scopes:
            if scp not in user_scp:
                raise TokenError("Missing scope for current access", 401)

    # provide data
    logging.info("Token decoded")
    return user, user_id, user_scp, local
