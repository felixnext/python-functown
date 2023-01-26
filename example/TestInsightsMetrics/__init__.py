"""
Example function to test metric logging capabilities of the application insights.

Copyright (c) 2023, Felix Geilert
"""

import logging
import json
import os
from random import random
from time import time
import sys
from typing import List

import azure.functions as func

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(dir_path, ".."))

import functown as ft  # noqa: E402


# retrieve the debug flag from the environment
DEBUG = ft.utils.get_flag("FUNC_DEBUG", False)
INST_KEY = ft.utils.get_config("APP_INSIGHTS_KEY", None)


@ft.ErrorHandler(
    debug=True,
    log_all_errors=DEBUG,
    return_errors=DEBUG,
    enable_logger=True,
    return_logs=True,
)
@ft.InsightsMetrics(
    instrumentation_key=INST_KEY,
    metrics=[
        ft.insights.MetricSpec(
            name="counter",
            description="A simple counter",
            unit="count",
            columns=["tag1", "tag2"],
            mtype=ft.insights.MetricType.COUNTER,
            dtype=int,
        ),
        ft.insights.MetricSpec(
            name="gauge",
            description="A simple gauge",
            unit="count",
            columns=["tag1", "tag4"],
            mtype=ft.insights.MetricType.GAUGE,
            dtype=float,
        ),
        ft.insights.MetricSpec(
            name="sum",
            description="summary of values",
            unit="grams",
            columns=["tag3", "tag5"],
            mtype=ft.insights.MetricType.SUM,
            dtype=float,
            start_value=0.5,
        ),
    ],
)
@ft.ArgsHandler()
def main(
    req: func.HttpRequest,
    args: ft.RequestArgHandler,
    logger: logging.Logger,
    logs: List[str],
    metrics: ft.insights.MetricHandler,
    **kwargs,
) -> func.HttpResponse:
    logger.info("Python HTTP trigger function processed a request.")

    # create a logger (allow to return log as list)
    logger.info(f"Using functown v{ft.__version__}")

    sleep_time = args.get_body_query("sleep", required=False, default=0, map_fct=float)
    logger.info(f"sleep time (sec): {sleep_time}")

    # check if counter should be updated
    cnum = args.get_body_query("counter", required=False, default=0, map_fct=int)
    counter = metrics["counter"]  # access via getitem
    for i in range(cnum):
        counter.record(1, tag1="a", tag2="b")
        logger.info(f"{i} - counter: {counter.data}")
        # check for sleep
        if sleep_time > 0:
            time.sleep(sleep_time)

    # check if gauge should be updated
    gnum = args.get_body_query("gauge", required=False, default=0, map_fct=int)
    gauge = metrics.gauge  # access via attribute
    for _ in range(gnum):
        gauge.record(random(), tag1="a", tag4="b")
        logger.info(f"gauge: {gauge.data}")
        # check for sleep
        if sleep_time > 0:
            time.sleep(sleep_time)

    # check if sum should be updated
    snum = args.get_body_query("sum", required=False, default=0, map_fct=int)
    summ = metrics.get_metric("sum")  # access via get_metric method
    for i in range(snum):
        summ.record(i, tag3="a", tag5="b")
        logger.info(f"{i} - sum: {summ.data}")
        # check for sleep
        if sleep_time > 0:
            time.sleep(sleep_time)

    # generate report
    payload = {
        "completed": True,
        "results": {
            "sleep_sec": sleep_time,
            "counter": {
                "hits": cnum,
                "data": counter.current_data,
                "time_series": counter.full_time_series,
            },
            "gauge": {
                "hits": gnum,
                "data": gauge.data,
            },
            "sum": {
                "hits": snum,
                "data": summ.current_data,
                "time_series": summ.full_time_series,
            },
        },
        "logs": logs,
    }
    return func.HttpResponse(
        json.dumps(payload), mimetype="application/json", status_code=200
    )
