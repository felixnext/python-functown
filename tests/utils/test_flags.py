"""Test for the flags parameters.

Copyright (c) 2023, Felix Geilert
"""


import os

import pytest

from functown.utils import get_config, get_flag


@pytest.mark.parametrize(
    "env, default, expected",
    [
        ({"CONFIG_A": "val1"}, None, "val1"),
        ({"CONFIG_A": "foo"}, None, "foo"),
        ({"CONFIG_A": "bar"}, None, "bar"),
        ({}, "test", "test"),
        ({}, None, None),
        ({"CONFIG_A": "val1", "CONFIG_B": "val2"}, "test", "val1"),
    ],
)
def test_get_config(env, default, expected):
    """Test the get_config function."""
    for key, value in env.items():
        os.environ[key] = value

    assert get_config("CONFIG_A", default) == expected

    for key in env.keys():
        del os.environ[key]


@pytest.mark.parametrize(
    "env, default, expected",
    [
        ({"FLAG_A": "True"}, False, True),
        ({"FLAG_A": "False"}, False, False),
        ({"FLAG_A": "true"}, False, True),
        ({"FLAG_A": "false"}, False, False),
        ({"FLAG_A": "1"}, False, True),
        ({"FLAG_A": "0"}, False, False),
        ({"FLAG_A": "yes"}, False, True),
        ({"FLAG_A": "no"}, False, False),
        ({"FLAG_A": "y"}, False, True),
        ({"FLAG_A": "n"}, False, False),
        ({"FLAG_A": "on"}, False, True),
        ({"FLAG_A": "off"}, False, False),
        ({"FLAG_A": "TRUE"}, False, True),
        ({"FLAG_A": "FALSE"}, False, False),
        ({"FLAG_A": "1"}, False, True),
        ({"FLAG_A": "0"}, False, False),
        ({"FLAG_A": "YES"}, False, True),
        ({"FLAG_A": "NO"}, False, False),
        ({"FLAG_A": "Y"}, False, True),
        ({"FLAG_A": "N"}, False, False),
        ({"FLAG_A": "ON"}, False, True),
        ({"FLAG_A": "OFF"}, False, False),
        ({"FLAG_A": "True", "FLAG_B": "False"}, False, True),
        ({"FLAG_A": "False", "FLAG_B": "True"}, False, False),
        ({"FLAG_A": "True", "FLAG_B": "True"}, False, True),
        ({"FLAG_A": "False", "FLAG_B": "False"}, False, False),
        ({}, False, False),
        ({}, True, True),
        ({"FLAG_C": "True", "FLAG_B": "True"}, False, False),
    ],
)
def test_get_flag(env, default, expected):
    """Test the get_flag function."""
    for key, value in env.items():
        os.environ[key] = value

    assert get_flag("FLAG_A", default) == expected

    for key in env.keys():
        del os.environ[key]
