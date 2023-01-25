"""Unit Tests for the insights.InsightsMetrics decorator

Copyright (c) 2023, Felix Geilert
"""

import logging
import json

import pytest
from azure.functions import HttpRequest, HttpResponse

from functown import InsightsMetrics
from functown.insights import filter_debug, MetricHandler, MetricType, MetricSpec


@pytest.mark.parametrize(
    "specs, callback, enable_perf",
    [
        (
            [
                MetricSpec(
                    name="dec_counter_metric_1",
                    description="first metric",
                    unit="count",
                    columns=["col1"],
                    mtype=MetricType.COUNTER,
                    dtype=int,
                )
            ],
            None,
            False,
        ),
        (
            [
                MetricSpec(
                    name="dec_counter_metric_2",
                    description="first metric",
                    unit="count",
                    columns=["col1"],
                    mtype=MetricType.COUNTER,
                    dtype=int,
                ),
                MetricSpec(
                    name="dec_gauge_metric_2",
                    description="first metric",
                    unit="value",
                    columns=["col3"],
                    mtype=MetricType.GAUGE,
                    dtype=float,
                ),
            ],
            None,
            False,
        ),
        (
            [
                MetricSpec(
                    name="dec_counter_metric_3",
                    description="first metric",
                    unit="count",
                    columns=["col1"],
                    mtype=MetricType.COUNTER,
                    dtype=int,
                )
            ],
            filter_debug,
            True,
        ),
    ],
    ids=[
        "minimal",
        "multi_metrics",
        "callback_perf",
    ],
)
def test_logger_decorator(caplog, specs, callback, enable_perf):
    """Tests the InsightsLogger decorator"""
    # FEAT: create proper mocking of AzureLogExporter (to test against filter)
    met_names = [m.name for m in specs]
    records = 10

    # create the decorator
    @InsightsMetrics(
        None,
        metrics=specs,
        callback=callback,
        enable_perf_metrics=enable_perf,
    )
    def test_func(req: HttpRequest, metrics: MetricHandler, *args, **kwargs):
        # retrieve a list of metrics
        mets = [metrics[m] for m in met_names]

        # count up the metrics
        for m in mets:
            for i in range(records):
                m.record(1)

        # add some data
        body = {
            name: {
                "data": met.current_data,
                "ts": [dp.value for dp in met.full_time_series],
            }
            for name, met in zip(met_names, mets)
        }

        return HttpResponse(
            json.dumps(body), status_code=200, mimetype="application/json"
        )

    # run the function
    with caplog.at_level(logging.INFO):
        res = test_func(HttpRequest(method="GET", url="/", body={}))

    # validate the logs (first message is always warning on insights)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == (
        "No instrumentation key provided. "
        "No data will be sent to Application Insights."
    )

    # check the response
    assert res is not None
    assert type(res) == HttpResponse
    assert res.status_code == 200

    # assert body
    data = json.loads(res.get_body())
    assert len(data) == len(met_names)
    for name, met in data.items():
        mtype = [m.mtype for m in specs if m.name == name][0]
        if mtype == MetricType.COUNTER:
            assert met["data"] == [records]
        elif mtype == MetricType.GAUGE:
            assert met["data"] == [1]
        assert len(met["ts"]) == 1
