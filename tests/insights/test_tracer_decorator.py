"""Unit Tests for the insights.InsightsTracer decorator

Copyright (c) 2023, Felix Geilert
"""

import logging
import sys

import pytest
from opencensus.trace.logging_exporter import LoggingExporter

from functown import InsightsTracer
from functown.insights import TracerObject


@pytest.mark.parametrize(
    "rate",
    [
        1.0,
        0.0,
        0.6,
    ],
    ids=[
        "full",
        "none",
        "middle",
    ],
)
def test_tracer_decorator(caplog, rate):
    """Tests the InsightsLogger decorator"""
    # FEAT: create proper mocking of AzureLogExporter (to test against filter)
    # create the decorator
    @InsightsTracer(None, sampling_rate=rate)
    def test_func(tracer: TracerObject, *args, **kwargs):
        # FEAT: validate proper exporter for the tracer (together with mocking)
        tracer.exporter = LoggingExporter(logging.StreamHandler(sys.stdout))
        with tracer.span("sample_span"):
            x = 1 + 3
            y = x + 1  # noqa: F841
        tracer.finish()

    # run the function
    with caplog.at_level(logging.INFO):
        test_func()

    # validate the logs (first message is always warning on insights)
    assert len(caplog.records) >= 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == (
        "No instrumentation key provided. "
        "No data will be sent to Application Insights (InsightsTracer)."
    )

    # check if rate is empty
    if rate == 0.0:
        assert len(caplog.records) == 1
        return

    # TODO: validate sampling
    # assert caplog.records[1].msg == "INFO"
