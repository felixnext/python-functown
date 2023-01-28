# FuncTown Documentation

## Philosophy

`FuncTown` follows the idea that Azure Functions should be atomic and do one thing well.
In that spirit the code of a single function should be as clear & structured as
possible and avoid boilerplate code.

Following this approach, means that Azure Functions are easier to test and maintain.
They are also easier readable by other developers.

This is why `FuncTown` is designed around the concept of decorators. It allows to
quickly add functionality to your function without having to modify the function itself.
As a result all functionality that is provided here (including argument parsing, error
handling, user-authentication, etc.) is mixed into Azure Functions through the use of
decorators.

> Note: All aspects of `FuncTown` make use of [type-hints](https://docs.python.org/3/library/typing.html),
> making the library easy to explore using IDEs like VSCode.

## Modules of FuncTown

`FuncTown` is split into multiple modules that provide different functionality.

### `functown.utils`

This provides a base set of utilities that are used by other modules. This includes:

* `BaseDecorator`: The decorator baseclass that helps maintain the signature of the
function, so that the Azure handlers can call them without problems
* `LogListHelper`: Log Exporter that takes a reference to a list and logs all items in
there for later reference.
* `get_config` and `get_flag`: Helper function to access environment variables

### `functown.args`

Contains functionality to parse arguments from the `HttpRequest` and provide them to
your function. The main decorator is:

```python
from functown.args import ArgsHandler, RequestArgHandler

@ArgsHandler()
def main(req: func.HttpRequest, args: RequestArgHandler, **kwargs) -> HttpResponse:
    # ...
    args.get_body_query("data_name", required=True, allowed=["foo", "bar"])
```

See [args-docs](argument-parsing.md) for more information.

### `functown.auth`

Contains functionality to handle authentication of users. The main decorator is:

```python
from functown.auth import AuthHandler, Token

@AuthHandler(scopes=["user.read"])
def main(req: HttpRequest, token: Token, **kwargs) -> HttpResponse:
    # ...
    logging.info(f"User: {token.user_id}")
```

See [auth-docs](authorization.md) for more information.

### `functown.errors`

Contains functionality to handle errors in Azure Functions. The main decorator is:

```python
from logging import Logger
from functown.errors import ErrorHandler

@ErrorHandler(enable_logger=True)
def main(req: HttpRequest, logger: Logger, **kwargs) -> HttpResponse:
    # ...
    raise Exception("Something went wrong")
```

See [errors-docs](error-handling.md) for more information.

### `functown.insights`

Contains functionality to handle logging of metrics to Application Insights. The main
decorator is:

```python
from logging import Logger
from functown.insights import Insights

@Insights(enable_logger=True, enable_events=True, enable_metrics=True, metrics=[
    MetricSpec(
        "metric_name", "metric_description", "metric_unit",
        columns=["tag1", "tag2"],
        mtype=ft.insights.MetricType.COUNTER,
        dtype=int
    )
])
def main(
    req: HttpRequest, logger: Logger, events: Logger, metrics: MetricHandler, **kwargs
) -> HttpResponse:
    # ...
    logger.info("Something happened")
    # ...
    events.info("Some event", extra={"custom_dimensions": {"foo": "bar"}})
    # ...
    metrics.metric_name.record(15)
```

See [insights-docs](insights.md) for more information.


### Stacking Decorators

All decorators can be stacked on top of each other. This allows you to combine
different functionality in a single function.

```python
from functown.auth import AuthHandler, Token
from functown.args import ArgsHandler, RequestArgHandler
from functown.errors import ErrorHandler
from functown.utils import StackDecorator

def dec_config() -> StackDecorator:
    return StackDecorator([
        ErrorHandler(enable_logger=True),
        AuthHandler(scopes=["user.read"]),
        ArgsHandler()
    ])

@dec_config()
def main(
    req: HttpRequest, token: Token, args: RequestArgHandler, logger: Logger, **kwargs
) -> HttpResponse:
    # ...
    logger.info(f"User: {token.user_id}")
    # ...
    args.get_body_query("data_name", required=True, allowed=["foo", "bar"])
```

This kind of stacking and configuration is helpful when you want to use the same set of
decorators in multiple functions or even across different function projects.

This is also highly recommended when you want to use the `functown.insights` module,
since it allows you to configure the metrics and events that are logged in a single
place.

## Help Developing

`FuncTown` is an open source project and we welcome contributions!

If you want to help extend `FuncTown` or fix a bug, you can do so by following the
[developer guide](dev-guide.md).
