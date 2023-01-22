"""Unit Tests for the insights.InsightsLogs decorator

Copyright (c) 2023, Felix Geilert
"""

import logging

import pytest
from pytest_mock.plugin import MockerFixture
from opencensus.ext.azure.log_exporter import AzureLogHandler

from functown import InsightsLogs
from functown.insights import filter_debug, create_filter_ids


@pytest.mark.parametrize(
    "send_basics, callback, clean_logger",
    [
        (False, None, False),
        (True, None, False),
        (True, None, True),
        (False, filter_debug, True),
        (False, create_filter_ids("123", ["123"]), True),
        (False, create_filter_ids("456", ["123"]), True),
    ],
    ids=[
        "minimal",
        "send_basics",
        "clean_logger",
        "callback",
        "filter_ids_true",
        "filter_ids_false",
    ],
)
# TODO: fix this test
@pytest.mark.skip
def test_logger_decorator(
    mocker: MockerFixture, caplog, send_basics, callback, clean_logger
):
    """Tests the InsightsLogger decorator"""
    # mock the AzureLogHandler
    mocker.patch.object(AzureLogHandler, "__init__", return_value=None)
    mocker.patch.object(AzureLogHandler, "add_telemetry_processor", return_value=None)

    # create the decorator
    @InsightsLogs(
        "inst_key",
        send_basics=send_basics,
        callback=callback,
        clean_logger=clean_logger,
    )
    def test_func(logger, *args, **kwargs):
        logger.info("test")

    # run the function
    with caplog.at_level(logging.INFO):
        test_func()

    # validate the logs
    assert len(caplog.records) == 1
    assert caplog.records[0].msg == "test"
