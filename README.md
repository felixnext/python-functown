# FuncTown

`FuncTown` is a python library to make working with azure functions easier and remove boilerplate.

## Getting Started

```
pip install functown
```

After installing you can easily get your functions error checked (with an auto-response for execptions triggered):

```python
from functown import handle_errors

@handle_errors(debug=True)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # ...

    return func.HttpResponse("success", status_code=200)
```

Should an exception happening in the middle, the decorator will auto-parse it (and write to logs if debug is true), then provide a response.

You can also parse JWT tokens and validate them (this currently requires to set the `B2C_ISSUER_URL` and `B2C_APP_ID` environment variables):

```python
from functown.auth import verify_user

def main(req: func.HttpRequest) -> func.HttpResponse:
    user, user_id, user_scp, local = verify_user(req, scope=scopes.SCOPE_WRITE)
```

Finally the library also allows you to easily parse arguments coming from the `HttpRequest`:

```python
from functown import RequestArgHandler

def main(req: func.HttpRequest) -> func.HttpResponse:
    args = RequestArgHandler(req)
    data = args.get_body_query("data_name", required=True, allowed=["foo", "bar"])
    switch = args.get_body("bool_name", map_fct='bool')
    file = args.get_file('file_name', required=True)
```

All this should remove boilerplate from Azure-Functions.

🎷 Welcome to FuncTown! 🎷
