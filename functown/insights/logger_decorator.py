"""Builds a logging handler for application insights.

This also provides a bunch of examples of callback_functions that can modify filter values.
It is also possible to run a custom compose of these filters and modifiers:

```python
def my_filter(envelop: Envelope) -> bool:
    if debug_filter(envelop):
        return False
    modify_system_info(envelop)
    return True
```

Examples how to use logger:

```python
# basic trace
logger.info("This is a log message")
# trace with extra data
logger.info("This is a log message", extra={"key": "value"})
# trace exception
ex = ...
logger.exception("Log found exception", exc_info=ex)
```

For a full guide on how to use the logger, see:
https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import Callable

from opencensus.ext.azure.log_exporter import (
    AzureLogHandler,
    Envelope,
)

from .base import InsightsDecorator


class InsightsLogs(InsightsDecorator):
    """Decorator that provides a sending interface to the Application Insights.

    This will add the `logger` object to the function call.

    Note that some default `callback` functions are defined in
    `functown.insights.callbacks`.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
        enable_logger (bool): Whether to enable the logger. Defaults to True.
        send_basics (bool): Whether to send basic metrics about the function.
            Defaults to False.
        callback (Callable[[Envelope], bool]): A callback function that is called for
            every telemetry item. It can act as a filter (by returning False) or modify
            the telemetry item (by returning True end modifying the reference to envelop
            passed).
        clean_logger (bool): Defines if existing `logger` object is overwritten.
            Defaults to False.
    """

    def __init__(
        self,
        instrumentation_key: str,
        send_basics: bool = True,
        callback: Callable[[Envelope], bool] = None,
        clean_logger: bool = False,
        **kwargs,
    ):
        super().__init__(instrumentation_key, added_kw=["logger"], **kwargs)

        self.send_basics = send_basics
        self.callback = callback
        self.clean_logger = clean_logger

    def run(self, func, *args, **kwargs):
        try:
            # check for logger
            logger = self._create_logger(self.clean_logger, "logger", *args, **kwargs)

            # create azure handler
            if self.instrumentation_key is not None:
                log_handler = AzureLogHandler(
                    connection_string=f"InstrumentationKey={self.instrumentation_key}"
                )
                if self.callback is not None:
                    log_handler.add_telemetry_processor(self.callback)
                logger.addHandler(log_handler)
            kwargs["logger"] = logger
        except Exception as ex:
            logging.error(f"Failed to create insights logger: {ex}")
            raise ex

        # execute main code
        try:
            # check for basics
            if self.send_basics:
                logger.info("Metric Setup Complete")

            # execute the main code
            return func(*args, **kwargs)
        except Exception as ex:
            # check for basics
            if self.send_basics:
                logger.exception("Function execution failed", exc_info=ex)

            # re-raise exception for outer loops
            raise ex
