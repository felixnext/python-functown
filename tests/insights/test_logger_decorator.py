"""Unit Tests for the insights.InsightsLogs decorator

Copyright (c) 2023, Felix Geilert
"""

import logging

import pytest

from functown import InsightsLogs
from functown.insights import filter_debug, create_filter_ids


@pytest.mark.parametrize(
    "send_basics, callback, create_logger, clean_logger",
    [
        (False, None, False, False),
        (True, None, False, False),
        (True, None, True, False),
        (True, None, True, True),
        (False, filter_debug, False, True),
        (False, create_filter_ids("123", ["123"]), False, True),
        (False, create_filter_ids("456", ["123"]), False, True),
    ],
    ids=[
        "minimal",
        "send_basics",
        "unclean_logger",
        "clean_logger",
        "callback",
        "filter_ids_true",
        "filter_ids_false",
    ],
)
def test_logger_decorator(caplog, send_basics, callback, create_logger, clean_logger):
    """Tests the InsightsLogger decorator"""
    # FEAT: create proper mocking of AzureLogExporter (to test against filter)
    # create the decorator
    @InsightsLogs(
        None,
        send_basics=send_basics,
        callback=callback,
        clean_logger=clean_logger,
    )
    def test_func(logger: logging.Logger, *args, **kwargs):
        logger.info("test")
        logger.info(f"name: {logger.name}")

    # run the function
    if create_logger is True:
        with caplog.at_level(logging.INFO):
            test_func(logger=logging.getLogger("test_logger"))
    else:
        with caplog.at_level(logging.INFO):
            test_func()

    # validate the logs (first message is always warning on insights)
    base_len = 3
    if send_basics:
        base_len += 1

    assert len(caplog.records) == base_len
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == (
        "No instrumentation key provided. "
        "No data will be sent to Application Insights (InsightsLogs)."
    )

    pos = 1

    if send_basics:
        assert caplog.records[pos].levelname == "INFO"
        assert caplog.records[pos].msg == "Metric Setup Complete"
        pos = 2

    assert caplog.records[pos].levelname == "INFO"
    assert caplog.records[pos].msg == "test"
    assert caplog.records[pos + 1].levelname == "INFO"
    log_name = (
        "InsightsLogs"
        if create_logger is False or clean_logger is True
        else "test_logger"
    )
    assert caplog.records[pos + 1].msg == f"name: {log_name}"
