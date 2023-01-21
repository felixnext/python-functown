"""
Example function using functown

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
INST_KEY = os.getenv("APP_INSIGHTS_KEY", None)


@ft.ErrorHandler(
    debug=True,
    log_all_errors=DEBUG,
    return_errors=DEBUG,
    enable_logger=True,
    return_logs=True,
)
@ft.InsightsEventHandler(
    instrumentation_key=INST_KEY,
    enable_events=True,
)
@ft.InsightsLogHandler(
    instrumentation_key=INST_KEY,
    enable_logger=True,
    clean_logger=False,
)
def main(
    req: func.HttpRequest,
    logger: logging.Logger,
    logs: List[str],
    events: logging.Logger,
    **kwargs,
) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger.info(f"Using functown v{ft.__version__}")

    # generate args parser
    args = ft.RequestArgHandler(req)

    # check if event should be logged
    use_event = args.get_body_query("use_event", False, "bool", default=False)
    if use_event is True:
        events.info("This is a test event")
        events.info(
            "This is a test event with a dict",
            extra={"custom_dimensions": {"test": "dict"}},
        )

    # generate sample logging messages
    use_logger = args.get_body_query("use_logger", False, "bool", default=False)
    if use_logger is True:
        logger.info("This is a test log")
        logger.info(
            "This is a test log with a dict",
            extra={"custom_dimensions": {"foo": "bar"}},
        )

    # generate report
    payload = {
        "completed": True,
        "results": {
            "use_event": use_event,
            "use_logger": use_logger,
        },
        "logs": logs,
    }
    return func.HttpResponse(
        json.dumps(payload), mimetype="application/json", status_code=200
    )
