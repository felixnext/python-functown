"""Combined Decorator for all insights elements.

Copyright (c) 2023, Felix Geilert
"""

from typing import Callable, List

from opencensus.ext.azure.log_exporter import Envelope

from .base import InsightsDecorator
from .metrics import MetricSpec
from .event_decorator import InsightsEvents
from .logger_decorator import InsightsLogs
from .metric_decorator import InsightsMetrics
from .tracer_decorator import InsightsTracer


class Insights(InsightsDecorator):
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

    def __init__(
        self,
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
        self.enable_logger = enable_logger
        self.send_basics = send_basics
        self.logger_callback = logger_callback
        self.clean_logger = clean_logger

        self.enable_events = enable_events
        self.event_callback = event_callback
        self.clean_events = clean_events

        self.enable_metrics = enable_metrics
        self.metrics = metrics

        self.enable_tracer = enable_tracer
        self.sampling_rate = sampling_rate

        decs = []
        if self.enable_logger:
            logger = InsightsLogs(
                instrumentation_key,
                send_basics=self.send_basics,
                callback=self.logger_callback,
                clean_logger=self.clean_logger,
            )
            decs.append(logger)

        if self.enable_events:
            events = InsightsEvents(
                instrumentation_key,
                callback=self.event_callback,
                clean_events=self.clean_events,
            )
            decs.append(events)

        if self.enable_metrics:
            metrics = InsightsMetrics(instrumentation_key, metrics=self.metrics)
            decs.append(metrics)

        if self.enable_tracer:
            tracer = InsightsTracer(
                instrumentation_key, sampling_rate=self.sampling_rate
            )
            decs.append(tracer)

        # set and expand
        self.__decs = decs
        kws = []
        for dec in self.__decs:
            kws.extend(dec.added_kw)

        super().__init__(instrumentation_key, added_kw=kws, **kwargs)

    def run(self, func, *args, **kwargs):
        # reverse order
        for dec in self.__decs[::-1]:
            func = dec(func)

        return func(*args, **kwargs)
