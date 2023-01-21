"""
Example function to test insights logging and tracing

Copyright (c) 2023, Felix Geilert
"""

from distutils.util import strtobool
import logging
import json
import os
from typing import List

import azure.functions as func
from opencensus.trace.tracer import Tracer

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
@ft.Insights(
    instrumentation_key=INST_KEY,
    enable_logger=True,
    send_basics=True,
    enable_tracer=True,
)
def main(
    req: func.HttpRequest,
    logger: logging.Logger,
    logs: List[str],
    tracer: Tracer,
    **kwargs,
) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger.info(f"Using functown v{ft.__version__}")

    # generate args parser
    args = ft.RequestArgHandler(req)

    # generate sample logging messages
    use_logger = args.get_body_query("use_logger", False, "bool", default=False)
    if use_logger is True:
        logger.info("This is a test log")
        logger.info(
            "This is a test log with a dict",
            extra={"custom_dimensions": {"foo": "bar"}},
        )

    # check if tracer should be used
    use_tracer = args.get_body_query("use_tracer", False, "bool", default=False)
    if use_tracer is True:
        # generate a span in which the entire stack trace is recorded and send to app insights
        with tracer.span(name="test_span") as span:
            span.add_attribute("test", "attribute")
            foo_val = 2
            bar_val = 10
            bar_bal = foo_val + bar_val  # noqa: F841

    # generate report
    payload = {
        "completed": True,
        "results": {
            "use_logger": use_logger,
            "use_tracer": use_tracer,
        },
        "logs": logs,
    }
    return func.HttpResponse(
        json.dumps(payload), mimetype="application/json", status_code=200
    )
