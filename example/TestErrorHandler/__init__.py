"""
Example function to test error handling capabilities.

Copyright (c) 2023, Felix Geilert
"""

from distutils.util import strtobool
import logging
import json
import os
from typing import List

import azure.functions as func

try:
    import functown_local as ft
except ImportError:
    import functown as ft


# retrieve the debug flag from the environment
DEBUG = bool(strtobool(os.getenv("FUNC_DEBUG", "False")))


@ft.ErrorHandler(
    debug=True,
    log_all_errors=DEBUG,
    return_errors=DEBUG,
    enable_logger=True,
    return_logs=True,
)
def main(
    req: func.HttpRequest,
    logger: logging.Logger,
    logs: List[str],
    **kwargs,
) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger.info(f"Using functown v{ft.__version__}")

    # generate args parser
    args = ft.RequestArgHandler(req)

    # check different parameters
    body_param = args.get_body("body_param", required=False, default="no body param")
    logger.info(f"body_param: {body_param}")
    query_param = args.get_query(
        "query_param", required=False, default="no query param"
    )
    logger.info(f"query_param: {query_param}")

    # check for exception (not that this includes a mapping function)
    use_exeption = args.get_body_query("use_exception", False, "bool", default=False)
    logger.info(f"use_exeption: {use_exeption}")
    if use_exeption:
        # this should raise an exception that is handled by the decorator
        logger.info("raising exception")
        raise Exception("This is a test exception")

    use_special_exc = args.get_body_query(
        "use_special_exception", False, "bool", default=False
    )
    logger.info(f"use_special_exc: {use_special_exc}")
    if use_special_exc:
        # this should raise an exception that is handled by the decorator
        logger.info("raising special exception")
        raise ft.errors.TokenError("Your token is invalid", 400)

    # retrieve numbers
    print_num = args.get_body_query("print_num", False, map_fct=int, default=0)
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
