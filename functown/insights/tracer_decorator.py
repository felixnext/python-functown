"""Decorator for tracing function calls inside of Application Insights.

Copyright (c) 2023, Felix Geilert
"""


import logging

from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from .base import InsightsDecorator


class InsightsTracer(InsightsDecorator):
    """Decorator that provides a sending interface to the Application Insights.

    This will add the `tracer` object to the function call.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
        sampling_rate (float): The sampling rate for the tracer. Defaults to 1.0.
    """

    def __init__(
        self,
        instrumentation_key: str,
        sampling_rate: float = 1.0,
        **kwargs,
    ):
        super().__init__(instrumentation_key, added_kw=["tracer"], **kwargs)

        self.sampling_rate = sampling_rate

    def run(self, func, *args, **kwargs):
        try:
            tracer = Tracer(
                exporter=AzureExporter(
                    connection_string=f"InstrumentationKey={self.instrumentation_key}"
                ),
                sampler=ProbabilitySampler(self.sampling_rate),
            )
            kwargs["tracer"] = tracer
        except Exception as ex:
            logging.error(f"Failed to create Insights Tracer: {ex}")
            raise ex

        return func(*args, **kwargs)
