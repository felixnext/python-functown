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

## Run Example

The source folder also includes an `example` function that provides a basic azure function,
that leverages the different functionality of the library.

You can create a new Functions app in your Azure Subscripton to test it. Follow these steps:

1. Create a new Functions App (note that this should at least be Python 3.8 and a consumption tier is recommended)
2. Publish the content of the example folder to the functions app (through VS Code Plug-In or through CLI)
3. Create a new Application Insights Instance through your Browser in the same resource group as the Functions App
4. Take the telemetry key from the App Insights and paste it to your

You can now use `curl` to test various commands against the endpoint:
