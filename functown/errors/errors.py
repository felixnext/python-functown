"""Range of custom errors required in functown.

Copyright (c) 2023, Felix Geilert
"""


class RequestError(Exception):
    """Basic Error for Azure Functions.

    Args:
        msg (str): Error message
        code (int, optional): Error code. Used to generate HttpResponse object.
            Defaults to 500.
    """

    def __init__(self, msg: str, code: int = None, *args: object) -> None:
        super().__init__(*args)
        self.msg = msg
        self.code = 500 if None else code

    def __str__(self) -> str:
        return f"Error ({self.code}): {self.msg}"


class HandlerError(RequestError):
    """Error within one of the decorator functions."""

    pass


class TokenError(RequestError):
    """Errors related to checking token.

    Usually used in the `auth` namespace
    """

    pass


class ArgError(RequestError):
    """Error related to parsing arguments."""

    pass
