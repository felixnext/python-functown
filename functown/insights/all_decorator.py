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
    """Decorator that combines functionality from LogHandler, MetricsHandler, TraceHandler and EventHandler."""

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
        super().__init__(instrumentation_key, added_kw=[], **kwargs)

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

    def run(self, func, *args, **kwargs):
        if self.enable_logger:
            logger = InsightsLogs(
                self.instrumentation_key,
                send_basics=self.send_basics,
                callback=self.logger_callback,
                clean_logger=self.clean_logger,
            )
            func = logger(func, *args, **kwargs)

        if self.enable_events:
            events = InsightsEvents(
                self.instrumentation_key,
                callback=self.event_callback,
                clean_events=self.clean_events,
            )
            func = events(func, *args, **kwargs)

        if self.enable_metrics:
            metrics = InsightsMetrics(self.instrumentation_key, metrics=self.metrics)
            metrics(func, *args, **kwargs)

        if self.enable_tracer:
            tracer = InsightsTracer(
                self.instrumentation_key, sampling_rate=self.sampling_rate
            )
            func = tracer(func, *args, **kwargs)

        return func(*args, **kwargs)
