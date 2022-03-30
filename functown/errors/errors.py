
class RequestError(Exception):
    def __init__(self, msg: str, code: int = None, *args: object) -> None:
        super().__init__(*args)
        self.msg = msg
        self.code = 500 if None else code


class HandlerError(RequestError):
    pass


class TokenError(RequestError):
    pass


class ArgError(RequestError):
    pass
