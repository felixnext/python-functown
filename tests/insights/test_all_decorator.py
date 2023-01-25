"""Unit Tests for the insights.Insights decorator

Copyright (c) 2023, Felix Geilert
"""

import logging

from azure.functions import HttpRequest, HttpResponse

from functown import Insights
from functown.insights import (
    TracerObject,
    MetricHandler,
    MetricSpec,
    MetricType,
)


def test_all_decorator(caplog):
    """Tests the InsightsLogger decorator"""
    # FEAT: create proper mocking of AzureLogExporter (to test against filter)
    # create the decorator
    @Insights(
        instrumentation_key=None,
        enable_logger=True,
        send_basics=True,
        enable_events=True,
        enable_tracer=True,
        enable_metrics=True,
        metrics=[
            MetricSpec(
                "dec_all_metric", "custom metric", "sample", [], MetricType.COUNTER, int
            )
        ],
    )
    def test_func(
        req: HttpRequest,
        logger: logging.Logger,
        events: logging.Logger,
        tracer: TracerObject,
        metrics: MetricHandler,
        *args,
        **kwargs,
    ):
        logger.info("test")
        logger.info(f"name: {logger.name}")
        events.info(f"event: {events.name}")
        events.info(f"event: {events.name}", extra={"custom_dimensions": {"test": 1}})
        with tracer.span("test"):
            x = 1 + 3
            y = x - 10  # noqa: F841
        met = metrics.get_metric("dec_all_metric")
        for i in range(10):
            met.record(1)
        data = met.current_data
        return HttpResponse(f"test: {data}", status_code=200, mimetype="text/plain")

    # run the function
    with caplog.at_level(logging.INFO):
        res = test_func(HttpRequest("GET", "http://localhost:7071/api/test", body=None))

    assert res is not None
    assert type(res) == HttpResponse
    assert res.status_code == 200
    assert res.mimetype == "text/plain"
    assert res.get_body() == b"test: [10]"

    assert len(caplog.records) == 10
    for i in range(5):
        assert caplog.records[i].levelname == "WARNING"
        assert caplog.records[i].msg == (
            "No instrumentation key provided. "
            "No data will be sent to Application Insights."
        )

    assert caplog.records[5].levelname == "INFO"
    assert caplog.records[5].msg == "Metric Setup Complete"
    assert caplog.records[6].msg == "test"
    assert caplog.records[6].name == "InsightsLogs"
    assert caplog.records[7].msg == "name: InsightsLogs"
    assert caplog.records[8].msg == "event: InsightsEvents"
    assert caplog.records[8].name == "InsightsEvents"
    assert caplog.records[9].msg == "event: InsightsEvents"
    assert caplog.records[9].custom_dimensions == {"test": 1}
