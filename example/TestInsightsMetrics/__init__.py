"""
Example function to test metric logging capabilities of the application insights.

Copyright (c) 2023, Felix Geilert
"""

from distutils.util import strtobool
import logging
import json
import os
from typing import List, Dict

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
@ft.InsightsMetrics(instrumentation_key=INST_KEY, metrics=[ft.insights.MetricSpec()])
def main(
    req: func.HttpRequest,
    logger: logging.Logger,
    logs: List[str],
    metrics: Dict[str, ft.insights.Metric],
    **kwargs,
) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger.info(f"Using functown v{ft.__version__}")

    # generate args parser
    args = ft.RequestArgHandler(req)

    # FIXME: define a bunch of metric tasks
    metrics["test_metric"].record(1)

    # generate report
    payload = {
        "completed": True,
        "results": {},
        "logs": logs,
    }
    return func.HttpResponse(
        json.dumps(payload), mimetype="application/json", status_code=200
    )
