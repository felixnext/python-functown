"""Predefined fixtures for serialization tests.

Copyright (c) 2023, Felix Geilert
"""

import pytest


@pytest.fixture()
def json_data():
    return {
        "infos": [
            {
                "msg": "Hello World",
                "id": 1,
                "score": 0.5,
                "data": [
                    {"msg": "Hello World 0", "type": "HIGH"},
                    {"msg": "Hello World 1", "type": "HIGH"},
                    {"msg": "Hello World 2", "type": "HIGH"},
                ],
            }
        ]
    }
