# Argument Parsing

The `ArgsHandler` decorator generates a `RequestArgHandler` object that can be used to
parse request arguments from various sources on the fly. This includes:

* files
* headers
* query parameters
* body parameters
* form parameters

```python
@ArgsHandler()
def main(req: func.HttpRequest, args: RequestArgHandler, **kwargs) -> HttpResponse:
    # ...
    args.get_body_query("data_name", required=True, allowed=["foo", "bar"])
```

The regarding get functions also provide a bunch of additional parameters that can be
used to post-process the parsed value.

```python
# get a bool from the query parameters
args.get_query("bool", map_fct="bool", default=True)

# get a file
args.get_file("file", required=True)

# get a parameter from either body or query that is in an allowed list
args.get_body_query("data_name", required=True, allowed=["foo", "bar"])

# parse a body parameter to int
args.get_body("int", map_fct=int, required=False, default=10)
```
