"""Decorator to log metrics to Azure Application Insights.

This also provides a bunch of examples of callback_functions that can modify filter values.
It is also possible to run a custom compose of these filters and modifiers:

```python
def my_filter(envelop: Envelope) -> bool:
    if debug_filter(envelop):
        return False
    modify_system_info(envelop)
    return True
```

Examples how to use logger and events:

```python
# basic trace
logger.info("This is a log message")
# trace with extra data
logger.info("This is a log message", extra={"key": "value"})
# trace exception
ex = ...
logger.exception("Log found exception", exc_info=ex)

# basic event
events.info("This is an event message")
# event with extra data
events.info("This is an event message", extra={"key": "value"})
```

For a full guide on how to use the logger, see:
https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python

Examples how to use tracing:

```python
# basic trace
with tracer.span("my_span"):
    # do something

# trace with extra data
with tracer.span("my_span", attributes={"key": "value"}):
    # do something
```

For more info on tracing, see:
https://opencensus.io/tracing/

Copyright (c) 2023, Felix Geilert
"""

import os
import sys
import logging
from typing import Callable

from azure.functions import HttpRequest, HttpResponse
from opencensus.ext.azure.log_exporter import (
    AzureLogHandler,
    Envelope,
    AzureEventHandler,
)
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer


def modify_system_info(envelop: Envelope) -> bool:
    """Appends System information (os, python, cpu, memory) to the message.

    Args:
        envelop (Envelope): The telemetry item.

    Returns:
        bool: Whether to keep the item.
    """
    system_info = (
        f"System: {sys.platform} {sys.version} {os.cpu_count()} {os.getloadavg()}"
    )
    envelop.data.base_data.message = f"{envelop.data.base_data.message} {system_info}"

    return True


def filter_debug(envelop: Envelope) -> bool:
    """Filter to remove debug messages from Azure Application Insights.

    Args:
        envelop (Envelope): The telemetry item.

    Returns:
        bool: Whether to keep the item.
    """
    if envelop.data.base_data.severity_level == 1:
        return False
    return True


def create_filter_ids(cur_id, ids: list) -> Callable[[Envelope], bool]:
    """Create a filter to remove specific ids from Azure Application Insights.

    Args:
        cur_id (str): The current id of the function.
        ids (list): A list of ids to remove.

    Returns:
        Callable[[Envelope], bool]: A filter function.
    """

    def filter_ids(envelop: Envelope) -> bool:
        """Filter to remove specific ids from Azure Application Insights.

        Args:
            envelop (Envelope): The telemetry item.

        Returns:
            bool: Whether to keep the item.
        """
        if cur_id in ids:
            return False
        return True

    return filter_ids


def create_filter_keywords(keywords: list) -> Callable[[Envelope], bool]:
    """Create a filter to remove specific keywords from Azure Application Insights.

    Args:
        keywords (list): A list of keywords to remove.

    Returns:
        Callable[[Envelope], bool]: A filter function.
    """

    def filter_keywords(envelop: Envelope) -> bool:
        """Filter to remove specific keywords from Azure Application Insights.

        Args:
            envelop (Envelope): The telemetry item.

        Returns:
            bool: Whether to keep the item.
        """
        for keyword in keywords:
            if keyword in envelop.data.base_data.message:
                return False
        return True

    return filter_keywords


def log_metrics(
    instrumentation_key: str,
    send_basics: bool = True,
    clean_logger: bool = False,
    logger_callback: Callable[[Envelope], bool] = None,
    enable_events: bool = True,
    event_callback: Callable[[Envelope], bool] = None,
    enable_tracer: bool = False,
    tracer_sample: float = 1.0,
    last_decorator: bool = False,
):
    """Decorator to log metrics to Azure Application Insights.

    Note that the `callback_function` is called for every telemetry item.
    It can act as a filter (by returning False) or modify the telemetry item
    (by returning True end modifying the reference to envelop passed).

    For a full guide on how to use the logger, see:
    https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights instance.
        send_basics (bool): Whether to send basic metrics about the function.
            Defaults to False.
        clean_logger (bool): Whether to clean the logger before adding the handler.
            Defaults to False.
        callback_function (Callable[[Envelope], bool]): A callback function to process the telemetry.
    """
    # check for instrumentation key
    if instrumentation_key is None:
        raise ValueError("No instrumentation key provided")

    def handle_fct(function):
        def execute(req: HttpRequest, *params, **kwargs) -> HttpResponse:
            # separate try-catch to create log handler
            try:
                # check for logger
                logger = kwargs.get("logger", None)
                if logger is None or clean_logger is True:
                    logging.debug(f"Creating logger for {function.__name__}")
                    logger = logging.getLogger(__name__)

                # create azure handler
                log_handler = AzureLogHandler(
                    connection_string=f"InstrumentationKey={instrumentation_key}"
                )
                if logger_callback is not None:
                    log_handler.add_telemetry_processor(logger_callback)
                logger.addHandler(log_handler)
                kwargs["logger"] = logger

                # create event handler
                if enable_events:
                    events = logging.getLogger("event_logger")
                    event_handler = AzureEventHandler(
                        connection_string=f"InstrumentationKey={instrumentation_key}"
                    )
                    if event_callback is not None:
                        event_handler.add_telemetry_processor(event_callback)
                    events.addHandler(event_handler)
                    kwargs["events"] = events

                # create tracer
                if enable_tracer:
                    tracer = Tracer(
                        exporter=AzureExporter(
                            connection_string=f"InstrumentationKey={instrumentation_key}"
                        ),
                        sampler=ProbabilitySampler(tracer_sample),
                    )
                    kwargs["tracer"] = tracer

                # TODO: integrate metrics
            except Exception as ex:
                logging.error(f"Failed to create Metrics Logger: {ex}")
                raise ex

            # execute main code
            try:
                # check for basics
                if send_basics:
                    logger.info("Metric Setup Complete")

                # execute the main code
                return function(req, *params, **kwargs)
            except Exception as ex:
                # check for basics
                if send_basics:
                    logger.exception("Function execution failed", exc_info=ex)

                # re-raise exception for outer loops
                raise ex

        # check for last decorator
        if last_decorator is True:
            return lambda req: execute(req)
        return execute

    return handle_fct
