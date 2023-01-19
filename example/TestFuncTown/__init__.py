"""
Example function using functown

Copyright (c) 2023, Felix Geilert
"""

from distutils.util import strtobool
import logging
import json
import os

import azure.functions as func
from functown import handle_errors, RequestArgHandler, __version__ as ft_version

from logging_helper import ListHandler


# retrieve the debug flag from the environment
DEBUG = bool(strtobool(os.getenv("FUNC_DEBUG", "False")))


@handle_errors(debug=True, log_all_errors=DEBUG, return_errors=DEBUG)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger = logging.getLogger("func_logger")
    logs = []
    logger.addHandler(ListHandler(logs))
    logger.info(f"Using functown v{ft_version}")

    # generate args parser
    args = RequestArgHandler(req)

    # check different parameters
    body_param = args.get_body("body_param", required=False, default="no body param")
    logger.info(f"body_param: {body_param}")
    query_param = args.get_query(
        "query_param", required=False, default="no query param"
    )
    logger.info(f"query_param: {query_param}")

    # check for exception (not that this includes a mapping function)
    # FIXME: the bool mapping throws an error if param is already a bool (passed in body)
    use_exeption = args.get_body_query("use_exception", False, "bool", default=False)
    logger.info(f"use_exeption: {use_exeption}")
    if use_exeption:
        # this should raise an exception that is handled by the decorator
        logger.info("raising exception")
        raise Exception("This is a test exception")

    # retrieve numbers
    # FIXME: this throws an error if the param is not given
    print_num = args.get_body_query("print_num", False, map_fct=int, default="0")
    logger.info(f"print_num: {print_num}")
    for i in range(print_num):
        logger.info(f"print_num: {i}")

    # retrieve list (from body only)
    print_list = args.get_body("print_list", False, default=[])
    logger.info(f"print_list: {print_list}")

    # check a required param
    req_param = args.get_body("req", True)
    logger.info(f"req_param: {req_param}")

    # generate report
    payload = {
        "completed": True,
        "results": {
            "body_param": body_param,
            "query_param": query_param,
            "use_exeption": use_exeption,
            "print_num": print_num,
            "print_list": print_list,
            "req_param": req_param,
        },
        "logs": logs,
    }
    return func.HttpResponse(
        json.dumps(payload), mimetype="application/json", status_code=200
    )
