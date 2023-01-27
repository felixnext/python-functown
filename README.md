# 🎷 FuncTown 🎷

[![PyPI Version](https://img.shields.io/pypi/v/functown.svg)](https://pypi.python.org/pypi/functown)
[![PyPI downloads](https://img.shields.io/pypi/dm/functown.svg)](https://pypistats.org/packages/functown)
![Packaging](https://github.com/felixnext/python-functown/actions/workflows/python-package.yml/badge.svg)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/functown.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/functown/)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

`FuncTown` is a python library that is designed to make your life with Azure Functions easier.

The core features of `FuncTown` are:

* **Error handling** - automatically handle errors and return a response to the user
* **Debugging** - Set debug flags that automatically return logs and traces as part of error responses from your function
* **JWT token validation** - automatically validate JWT tokens and provide the user information
* **Request argument parsing** - automatically parse arguments from the `HttpRequest` and provide them to your function
* **Metrics** - Handle connections to Application Insights and gives you easy to use metrics objects
* **Logging, Tracing & Events** - Log your functions data directly into Application Insights

For detailed features see the [docs](docs/overview.md).

## Getting Started

You can install `FuncTown` using `pip`:

```bash
pip install functown
```

Almost all functionality of `FuncTown` is provided through decorators.
If you want to add error handling to your function:

```python
from logging import Logger
from functown import ErrorHandler

@ErrorHandler(debug=True, enable_logger=True)
def main(req: func.HttpRequest, logger: Logger, **kwargs) -> func.HttpResponse:
    logger.info('Python HTTP trigger function processed a request.')

    # ...
    # exception will be caught and handled by the decorator (returning a 500)
    raise ValueError("something went wrong")

    return func.HttpResponse("success", status_code=200)
```

> Note: Decorators might pass down additional arguments to your function,
> so it is generally a good idea to modify your function signature to accept these
> arguments (see [docs](docs/overview.md) for more information) and add a `**kwargs`
> to the end.

Decorators are also stackable, so we could parse function arguments and handle a JWT
Token in the same function:

```python
from functown import ArgsHandler, RequestArgHandler, AuthHandler
from functown.auth import Token

@ArgsHandler()
@AuthHandler(scopes=["user.read"])
def main(
    req: func.HttpRequest, args: RequestArgHandler, token: Token
) -> func.HttpResponse:
    # retrieve some arguments
    data = args.get_body_query("data_name", required=True, allowed=["foo", "bar"])
    switch = args.get_body("bool_name", map_fct='bool')
    file = args.get_file('file_name', required=True)

    # check the user id
    user_id = token.user_id

    # ...
```

This would also directly fail with a `400` message if there is no token provided,
or the token does not contain the required scopes.

Be sure to check out the [docs](docs/overview.md) for a full overview of all
decorators.

If you want to test it on your own Azure Subscription, you can check out the
[example guide](docs/dev-guide.md#setting-up-the-function-app) in the dev section of the
docs.

🎷 Welcome to FuncTown! 🎷

## Note

‼️ If you find this library helpful or have suggestions please let me know.
Also any contributions are welcome! ‼️

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/felixnext)