"""Combined Decorator for all insights elements.

Copyright (c) 2023, Felix Geilert
"""

from typing import Callable, List

from opencensus.ext.azure.log_exporter import Envelope

from functown.utils import StackDecorator

from .metrics import MetricSpec
from .event_decorator import InsightsEvents
from .logger_decorator import InsightsLogs
from .metric_decorator import InsightsMetrics
from .tracer_decorator import InsightsTracer


def insights(
    instrumentation_key: str,
    enable_logger: bool = False,
    send_basics: bool = False,
    logger_callback: Callable[[Envelope], bool] = None,
    clean_logger: bool = False,
    enable_events: bool = False,
    event_callback: Callable[[Envelope], bool] = None,
    clean_events: bool = False,
    enable_metrics: bool = False,
    metrics: List[MetricSpec] = None,
    enable_tracer: bool = False,
    sampling_rate: float = 1.0,
    **kwargs,
):
    """Decorator that combines functionality from LogHandler, MetricsHandler,
    TraceHandler and EventHandler.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
        enable_logger (bool): Whether to enable logging to Application Insights.
            Defaults to `False`.
        send_basics (bool): Whether to send basic information about the function call
            to Application Insights. Defaults to `False`.
        logger_callback (Callable[[Envelope], bool]): A callback function that is called
            after the logger has been called. Defaults to `None`.
        clean_logger (bool): Whether to clean the logger after the function call.
            Defaults to `False`.
        enable_events (bool): Whether to enable events to Application Insights.
            Defaults to `False`.
        event_callback (Callable[[Envelope], bool]): A callback function that is called
            after the event has been called. Defaults to `None`.
        clean_events (bool): Whether to clean the events after the function call.
            Defaults to `False`.
        enable_metrics (bool): Whether to enable metrics to Application Insights.
            Defaults to `False`.
        metrics (List[MetricSpec]): A list of metrics to be logged. Defaults to `None`.
        enable_tracer (bool): Whether to enable tracing to Application Insights.
            Defaults to `False`.
        sampling_rate (float): The sampling rate for the tracer. Defaults to `1.0`.
    """
    decs = []
    if enable_logger:
        logger = InsightsLogs(
            instrumentation_key,
            send_basics=send_basics,
            callback=logger_callback,
            clean_logger=clean_logger,
        )
        decs.append(logger)

    if enable_events:
        events = InsightsEvents(
            instrumentation_key,
            callback=event_callback,
            clean_events=clean_events,
        )
        decs.append(events)

    if enable_metrics:
        metrics = InsightsMetrics(instrumentation_key, metrics=metrics)
        decs.append(metrics)

    if enable_tracer:
        tracer = InsightsTracer(instrumentation_key, sampling_rate=sampling_rate)
        decs.append(tracer)

    return StackDecorator(decs)


def Insights(
    instrumentation_key: str,
    enable_logger: bool = False,
    send_basics: bool = False,
    logger_callback: Callable[[Envelope], bool] = None,
    clean_logger: bool = False,
    enable_events: bool = False,
    event_callback: Callable[[Envelope], bool] = None,
    clean_events: bool = False,
    enable_metrics: bool = False,
    metrics: List[MetricSpec] = None,
    enable_tracer: bool = False,
    sampling_rate: float = 1.0,
    **kwargs,
):
    """DEPRECATED: use insights instead (will be removed in v2.0.0).

    Decorator that combines functionality from LogHandler, MetricsHandler,
    TraceHandler and EventHandler.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
        enable_logger (bool): Whether to enable logging to Application Insights.
            Defaults to `False`.
        send_basics (bool): Whether to send basic information about the function call
            to Application Insights. Defaults to `False`.
        logger_callback (Callable[[Envelope], bool]): A callback function that is called
            after the logger has been called. Defaults to `None`.
        clean_logger (bool): Whether to clean the logger after the function call.
            Defaults to `False`.
        enable_events (bool): Whether to enable events to Application Insights.
            Defaults to `False`.
        event_callback (Callable[[Envelope], bool]): A callback function that is called
            after the event has been called. Defaults to `None`.
        clean_events (bool): Whether to clean the events after the function call.
            Defaults to `False`.
        enable_metrics (bool): Whether to enable metrics to Application Insights.
            Defaults to `False`.
        metrics (List[MetricSpec]): A list of metrics to be logged. Defaults to `None`.
        enable_tracer (bool): Whether to enable tracing to Application Insights.
            Defaults to `False`.
        sampling_rate (float): The sampling rate for the tracer. Defaults to `1.0`.
    """
    return insights(
        instrumentation_key,
        enable_logger=enable_logger,
        send_basics=send_basics,
        logger_callback=logger_callback,
        clean_logger=clean_logger,
        enable_events=enable_events,
        event_callback=event_callback,
        clean_events=clean_events,
        enable_metrics=enable_metrics,
        metrics=metrics,
        enable_tracer=enable_tracer,
        sampling_rate=sampling_rate,
        **kwargs,
    )
