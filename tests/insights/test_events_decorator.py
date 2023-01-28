"""Unit Tests for the insights.InsightsEvents decorator

Copyright (c) 2023, Felix Geilert
"""

import logging

import pytest

from functown import InsightsEvents
from functown.insights import filter_debug, create_filter_ids


@pytest.mark.parametrize(
    "callback, create_logger, clean_logger",
    [
        (None, False, False),
        (None, True, False),
        (None, True, True),
        (filter_debug, False, True),
        (create_filter_ids("123", ["123"]), False, True),
        (create_filter_ids("456", ["123"]), False, True),
    ],
    ids=[
        "minimal",
        "unclean_logger",
        "clean_logger",
        "callback",
        "filter_ids_true",
        "filter_ids_false",
    ],
)
def test_events_decorator(caplog, callback, create_logger, clean_logger):
    """Tests the InsightsLogger decorator"""
    # FEAT: create proper mocking of AzureLogExporter (to test against filter)
    # create the decorator
    @InsightsEvents(
        None,
        callback=callback,
        clean_logger=clean_logger,
    )
    def test_func(events: logging.Logger, *args, **kwargs):
        events.info("test", extra={"custom_dimensions": {"name": "test"}})
        events.info(f"name: {events.name}")

    # run the function
    if create_logger is True:
        with caplog.at_level(logging.INFO):
            test_func(events=logging.getLogger("test_events"))
    else:
        with caplog.at_level(logging.INFO):
            test_func()

    # validate the logs (first message is always warning on insights)
    base_len = 3

    assert len(caplog.records) == base_len
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == (
        "No instrumentation key provided. "
        "No data will be sent to Application Insights (InsightsEvents)."
    )

    pos = 1

    assert caplog.records[pos].levelname == "INFO"
    assert caplog.records[pos].msg == "test"
    assert caplog.records[pos + 1].levelname == "INFO"
    log_name = (
        "InsightsEvents"
        if create_logger is False or clean_logger is True
        else "test_events"
    )
    assert caplog.records[pos + 1].msg == f"name: {log_name}"
