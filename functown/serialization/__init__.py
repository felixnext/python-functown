import logging

from .base import SerializationDecorator, DeserializationDecorator
from .choice import ChoiceDecorator
from .json import JsonResponse, JsonRequest

try:
    from .flatbuf import FlatbufResponse, FlatbufRequest
except ImportError:
    logging.warning(
        "Unable to load flatbuffers, please install `functown[flatbuffers]`"
    )

try:
    from .protobuf import ProtobufResponse, ProtobufRequest
except ImportError:
    logging.warning("Unable to load protobuf, please install `functown[protobuf]`")
