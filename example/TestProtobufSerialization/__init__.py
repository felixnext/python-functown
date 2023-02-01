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
from . import example_pb2 as pb2


DEBUG = ft.utils.get_flag("FUNC_DEBUG", False)


@ft.ErrorHandler(DEBUG, log_all_errors=DEBUG, enable_logger=True, return_logs=DEBUG)
@ft.serialization.ProtobufRequest(pb_class=pb2.InformationList)
@ft.serialization.ProtobufResponse(pb_class=pb2.InformationList, allow_json=True)
def main(req: HttpRequest, body: pb2.InformationList, logger: Logger, **kwargs) -> dict:
    # show the retrieved data
    logger.info(f"retrieved: {type(body)}")
    logger.info(f"Msg: {body.infos[0].id}:{body.infos[0].msg} - {body.infos[0].score}")

    # generate a new information list from json
    return {"infos": [{"id": 2, "msg": "Hello World 2", "score": 0.5, "data": []}]}
