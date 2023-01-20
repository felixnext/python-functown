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

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Callable, Dict, Union, Type

from azure.functions import HttpRequest, HttpResponse
from opencensus.ext.azure.log_exporter import (
    AzureLogHandler,
    Envelope,
    AzureEventHandler,
)
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.azure import metrics_exporter
from opencensus.tags import tag_map as tag_map_module
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module


# FIXME: refactor this into separate decorators


def metrics_all(
    instrumentation_key: str,
    enable_logger: bool = True,
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
                if enable_logger:
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
                # FEAT: make sure that metrics allow for counters and timers
                # FEAT: esp allow to log counter features (e.g. click rates based on properties)
                # setup the view manager and the exporter
                """vm_metrics = stats_module.stats.view_manager
                exporter = metrics_exporter.new_metrics_exporter(
                    connection_string=f"InstrumentationKey={instrumentation_key}"
                )
                vm_metrics.register_exporter(exporter)
                measure_module.MeasureInt()
                tmap = tag_map_module.TagMap()
                tmap."""
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


# create a list of sub decorators for each of the functionality (logger, events, tracer, metrics) as wrappers around metrics_all


def metrics_logger(
    intrumentation_key: str,
    send_basics: bool = True,
    logger_callback: Callable[[Envelope], bool] = None,
    clean_logger: bool = False,
    last_decorator: bool = False,
):
    """Decorator to log Trace to Azure Application Insights through `logger` object."""
    return metrics_all(
        intrumentation_key,
        enable_logger=True,
        send_basics=send_basics,
        logger_callback=logger_callback,
        clean_logger=clean_logger,
        enable_events=False,
        enable_tracer=False,
        last_decorator=last_decorator,
    )


def metrics_events(
    instrumentation_key: str,
    event_callback: Callable[[Envelope], bool] = None,
    last_decorator: bool = False,
):
    """Decorator to log CustomEvent to Azure Application Insights through `events` object."""
    return metrics_all(
        instrumentation_key,
        enable_logger=False,
        enable_events=True,
        event_callback=event_callback,
        enable_tracer=False,
        last_decorator=last_decorator,
    )


def metrics_tracer(
    instrumentation_key: str,
    tracer_sample: float = 1.0,
    last_decorator: bool = False,
):
    """Decorator to log Trace to Azure Application Insights through `tracer` object."""
    return metrics_all(
        instrumentation_key,
        enable_logger=False,
        enable_events=False,
        enable_tracer=True,
        tracer_sample=tracer_sample,
        last_decorator=last_decorator,
    )
