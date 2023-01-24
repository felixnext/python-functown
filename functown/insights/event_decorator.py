"""Decorator to send events to Application Insights.

This also provides a bunch of examples of callback_functions that can modify filter values.
It is also possible to run a custom compose of these filters and modifiers:

```python
def my_filter(envelop: Envelope) -> bool:
    if debug_filter(envelop):
        return False
    modify_system_info(envelop)
    return True
```

Examples how to use events:

```python
# basic event
events.info("This is an event message")
# event with extra data
events.info("This is an event message", extra={"key": "value"})
```

For a full guide on how to use the event logger, see:
https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import Callable

from opencensus.ext.azure.log_exporter import (
    AzureEventHandler,
    Envelope,
)

from .base import InsightsDecorator


class InsightsEvents(InsightsDecorator):
    """Decorator to send events to Application Insights.

    This will add the `events` object to the function call.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
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
        callback: Callable[[Envelope], bool] = None,
        clean_logger: bool = False,
        **kwargs,
    ):
        super().__init__(instrumentation_key, added_kw=["events"], **kwargs)

        self.callback = callback
        self.clean_logger = clean_logger

    def run(self, func, *args, **kwargs):
        try:
            events = self._create_logger(self.clean_logger, "events", *args, **kwargs)

            if self.instrumentation_key is not None:
                event_handler = AzureEventHandler(
                    connection_string=f"InstrumentationKey={self.instrumentation_key}"
                )
                if self.callback is not None:
                    event_handler.add_telemetry_processor(self.callback)
                events.addHandler(event_handler)
            kwargs["events"] = events
        except Exception as ex:
            logging.error(f"Failed to create Insights Events Logger: {ex}")
            raise ex

        return func(*args, **kwargs)
