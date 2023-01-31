"""
Example function to test serialization

Copyright (c) 2023, Felix Geilert
"""

from logging import Logger
import os
import sys

from azure.functions import HttpRequest

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(dir_path, ".."))

import functown as ft  # noqa: E402


DEBUG = ft.utils.get_flag("FUNC_DEBUG", False)

# TODO: load the protobuf schema from a file
@ft.ErrorHandler(DEBUG, log_all_errors=DEBUG, enable_logger=True, return_logs=DEBUG)
@ft.serialization.ProtobufRequest()
@ft.serialization.ProtobufResponse()
def main(req: HttpRequest, body: dict, logger: Logger, **kwargs) -> dict:
    logger.info(f"Received request: {body}")
    body["processed"] = True
    return body
