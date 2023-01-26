# Error Handling

The error handler captures the entire function code into a try-except block and handles
any errors that occur. You can thereby specify with flags how you want to handle the
errors.

```python
from functown.errors import ErrorHandler

@ErrorHandler(enable_logger=True)
def main(req: HttpRequest, logger: Logger, **kwargs) -> HttpResponse:
    # ...
    raise Exception("Something went wrong")
```

Appart from the error handling, this creates a logger object that you can use in your
code. If `return_logs` is enabled all logs from this logger are returned in the
response.

The `functown.errors` module also contains a special `RequestError` class and
derivatives from it. These errors allow to pass a message and a status_code, which will
get picked up by the `ErrorHandler` to generate a regarding `HttpResponse`.

Regular errors on the other hand will be logged and a `500` status code will be
returned. There are additional flags that you can set, to return the trace of the error
and the logs from the system (if `return_logs` and `enable_logger` is activated) in the
response for debugging purposes.

It is usually advised to use the `functown.utils.get_flag` functionality to control this
behavior through the Azure Function configuration:

```python
from functown.utils import get_flag
from functown.errors import ErrorHandler

DEBUG = get_flag("FUNC_DEBUG", default=False)

@ErrorHandler(
    debug=True,
    log_all_errors=DEBUG
    enable_logger=True,
    return_logs=DEBUG,
)
def main(req: HttpRequest, logger: Logger, **kwargs) -> HttpResponse:
    # ...
    raise Exception("Something went wrong")
```

The parameters are as follows:

* `debug`: If set to `True` the error handler will return debugging information for
    regular errors.
* `log_all_errors`: If set to `True` the error handler will return debugging information
    for `RequestErrors` as well.
* `return_errors`: If set to `True` the error handler will return the trace of the error
    in the response.
* `return_logs`: If set to `True` the error handler will return the logs from the system
    in the response.
* `enable_logger`: If set to `True` the error handler will create a logger object that
    you can use in your code.
* `clean_logger`: If set to `True` the error handler will create a new logger object
    even if a previous decorator has already created one.
* `general_error_msg`: Allows to customize the error message if no debug information is
    returned.