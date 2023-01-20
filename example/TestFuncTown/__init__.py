"""
Example function using functown

Copyright (c) 2023, Felix Geilert
"""

from distutils.util import strtobool
import logging
import json
import os

import azure.functions as func

try:
    import functown_local as ft
except ImportError:
    import functown as ft

from logging_helper import ListHandler


# retrieve the debug flag from the environment
DEBUG = bool(strtobool(os.getenv("FUNC_DEBUG", "False")))
INST_KEY = os.getenv("APP_INSIGHTS_KEY", None)


@ft.clean()
@ft.handle_errors(debug=True, log_all_errors=DEBUG, return_errors=DEBUG)
@ft.log_metrics(instrumentation_key=INST_KEY, send_basics=True)
def main(
    req: func.HttpRequest, logger: logging.Logger, events: logging.Logger, **kwargs
) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logs = []
    logger.addHandler(ListHandler(logs))
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

    # check if metric should be logged
    use_metric = args.get_body_query("use_metric", False, "bool", default=False)
    if use_metric is True:
        # FIXME: update this
        logger.error("Not implemented yet!")

    # check if event should be logged
    use_event = args.get_body_query("use_event", False, "bool", default=False)
    if use_event is True:
        events.info("This is a test event")
        events.info("This is a test event with a dict", extra={"test": "dict"})

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