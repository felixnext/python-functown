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

import logging
from typing import List

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

from .base import InsightsDecorator
from .metrics import MetricSpec, MetricType, Metric


class InsightsMetrics(InsightsDecorator):
    """Decorator to log metrics to Azure Application Insights."""

    def __init__(
        self,
        instrumentation_key: str,
        metrics: List[MetricSpec],
        **kwargs,
    ):
        super().__init__(instrumentation_key, kwargs=["metrics"], **kwargs)

        self.metric_specs = metrics

    def run(self, func, *args, **kwargs):
        try:
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

        try:
            metrics = []
            for metric_spec in self.metric_specs:
                metric = Metric(metric_spec)
                metrics.append(metric)
            kwargs["metrics"] = metrics
        except Exception as ex:
            logging.error(f"Failed to create Insights Metrics: {ex}")
            raise ex

        return func(*args, **kwargs)
