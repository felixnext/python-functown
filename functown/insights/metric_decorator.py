"""Decorator to log metrics to Azure Application Insights.

An example of how to use this decorator:

```python
from functown import InsightsMetrics

@InsightsMetrics(
    instrumentation_key="...",
    metrics=[
        MetricSpec(
            name="my_metric",
            description="My metric",
            unit="count",
            aggregation_type=MetricType.COUNTER,
            dtype=int,
        ),
    ],
)
def my_function(metrics):
    # ...
    metrics["my_metric"].record(1)
    # ...
```

Copyright (c) 2023, Felix Geilert
"""

import logging
from typing import List, Callable

from opencensus.ext.azure import metrics_exporter
from opencensus.stats import stats as stats_module

from .base import InsightsDecorator
from .metrics import MetricSpec, Metric


class InsightsMetrics(InsightsDecorator):
    """Decorator to log metrics to Azure Application Insights.

    This will add the `metrics` object to the function call.

    Args:
        instrumentation_key (str): The instrumentation key for the Application Insights.
        metrics (List[MetricSpec]): A list of metrics to be logged.
        enable_perf_metrics (bool): Whether to enable performance metrics to be send
            to Application Insights. Defaults to `True`.
        enable_name_column (bool): Whether to enable the `__name` column is
            automatically added to the metrics. Defaults to `False`.
    """

    def __init__(
        self,
        instrumentation_key: str,
        metrics: List[MetricSpec],
        callback: Callable[[metrics_exporter.Envelope], None] = None,
        enable_perf_metrics: bool = True,
        enable_name_column: bool = False,
        **kwargs,
    ):
        super().__init__(instrumentation_key, kwargs=["metrics"], **kwargs)

        self.metric_specs = metrics
        self.callback = callback
        self.perf_metrics = enable_perf_metrics
        self.enable_name_column = enable_name_column

    def run(self, func, *args, **kwargs):
        try:
            # define the view manager
            vm = stats_module.stats.view_manager

            # generate metrics
            metrics = dict(
                [
                    (m.name, Metric(m, vm, self.enable_name_column))
                    for m in self.metric_specs
                ]
            )
            kwargs["metrics"] = metrics

            # register exporter for the metrics
            exporter = metrics_exporter.new_metrics_exporter(
                enable_standard_metrics=self.perf_metrics,
                connection_string=f"InstrumentationKey={self.instrumentation_key}",
            )
            if self.callback is not None:
                exporter.add_telemetry_processor(self.callback)
            vm.register_exporter(exporter)
        except Exception as ex:
            logging.error(f"Failed to create Metrics Logger: {ex}")
            raise ex

        return func(*args, **kwargs)
