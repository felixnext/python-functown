"""Test the LogListHandler class for logging.

Copyright (c) 2023, Felix Geilert
"""

import logging

import pytest

from functown.utils import LogListHandler


@pytest.mark.parametrize(
    "items, level",
    [
        ([("test", logging.INFO)], logging.INFO),
        ([("test", logging.INFO)], logging.DEBUG),
        ([("test", logging.INFO), ("test2", logging.INFO)], logging.INFO),
        ([("test", logging.INFO), ("test2", logging.INFO)], logging.DEBUG),
    ],
    ids=[
        "simple_info",
        "simple_filter",
        "multiple_info",
        "multiple_filter",
    ],
)
def test_log_list_handler(items, level):
    """Test the LogListHandler class."""
    # create a logger
    logger = logging.getLogger("test")
    logger.setLevel(level)

    logs = []
    logger.addHandler(LogListHandler(logs))

    # log some messages
    for msg, lvl in items:
        logger.log(lvl, msg)

    # filter the message according to level
    filtered = [msg for msg, lvl in items if lvl >= level]

    # check if the logs are correct
    assert len(logs) == len(filtered)
    assert logs == filtered
