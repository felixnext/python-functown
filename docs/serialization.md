# Serialization

Serialization decorators allow to easily serialize and deserialize data to and from
specific formats.

## JSON Decorators

This is supported out of the box by `functown`.

### Serialization

In this case the `main` function will not return a `HttpResponse` object but a data
object. The decorator will automatically serialize the data object to the specified
format and modify the function to return a `HttpResponse` object.

```python
from functown.serialization import JsonResponse

@JsonResponse
def main(req: HttpRequest):
    return {'foo': 'bar'}
```

> Note: Currently only `JsonResponse` is implemented. But `SerializationDecorator` can
> be easily extended to support other formats.

### Deserialization

In this case the `main` function will receive an additional `body` argument containing
the deserialized data object. The decorator will automatically deserialize the request
body to the specified format and modify the function to receive a `body` argument.

```python
from functown.serialization import JsonRequest

@JsonRequest
def main(req: HttpRequest, body: dict):
    item = body['item']
    # ...
```

> Note: Currently only `JsonRequest` is implemented. But `DeserializationDecorator` can
> be easily extended to support other formats.


## Protocol Buffers Decorators

This requires an extra package to pull in protobuf dependencies:

```bash
pip install functown[protobuf]
```

### Serialization

TODO

### Deserialization

TODO


## Flatbuffers Decorators

This requires an extra package to pull in flatbuffers dependencies:

```bash
pip install functown[flatbuffer]
```

### Serialization

TODO

### Deserialization

TODO


## Pandas Decorators

This requires an extra package to pull in pandas dependencies:

```bash
pip install functown[pandas]
```

### Serialization

TODO

### Deserialization

TODO
