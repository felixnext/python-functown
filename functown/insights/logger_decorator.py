"""Builds a logging handler for application insights.

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import Callable

from .base import InsightsDecorator


class InsightsLogs(InsightsDecorator):
    """Decorator that provides a sending interface to the Application Insights."""

    def __init__(
        self,
        instrumentation_key: str,
        enable_logger: bool = True,
        callback: Callable[[Envelope], bool] = None,
        clean_logger: bool = False,
        **kwargs
    ):
        super().__init__(None, **kwargs)
