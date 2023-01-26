# Authorization

The authorization decorator allows to restrict access to your function to requests that
provide a valid bearer token. This JWT token can then be parsed and returned as a
`Token` object.

The decorator can also directly check the scopes of the token and return a 400 if the
required scopes are not present.

```python
from functown.auth import AuthHandler, Token

@AuthHandler(scopes=["user.read"])
def main(req: HttpRequest, token: Token, **kwargs) -> HttpResponse:
    # ...
    logging.info(f"User: {token.user_id}")
```

Additionally if you provide the public key and the url of the token issuer, the
decorator can verify the token against the backend.

```python
from functown.auth import AuthHandler, Token
from functown.utils import get_config

@AuthHandler(
    scopes=["user.read"],
    audience=get_config("APP_ID"),
    issuer=get_config("ISSUER"),
)
def main(req: HttpRequest, token: Token, **kwargs) -> HttpResponse:
    # ...
    logging.info(f"User: {token.user_id}")
```

> Note here that `get_config` reads the information from the environment variables.
> These are specified in the `configuration` blade of your Azure Function.
