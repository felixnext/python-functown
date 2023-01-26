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
from typing import List, Callable, Dict, Any

from opencensus.ext.azure import metrics_exporter

from .base import InsightsDecorator
from .metrics import MetricHandler, MetricSpec, MetricUseMode


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
        global_columns (Dict[str, Any]): A dictionary of columns that will be added
            to all metrics. Defaults to `None`.
        hard_fail (bool): Whether to hard fail if the metrics cannot be created.
            Defaults to `True`.
        flush_seconds (float): Interval (seconds) in which the metrics are flushed
            to Application Insights. Defaults to `15`.
    """

    def __init__(
        self,
        instrumentation_key: str,
        metrics: List[MetricSpec],
        callback: Callable[[metrics_exporter.Envelope], None] = None,
        enable_perf_metrics: bool = True,
        enable_name_column: bool = False,
        global_columns: Dict[str, Any] = None,
        mode: MetricUseMode = MetricUseMode.REUSE,
        flush_seconds: float = 15,
        **kwargs,
    ):
        super().__init__(instrumentation_key, added_kw=["metrics"], **kwargs)

        self.metric_specs = metrics
        self.callback = callback
        self.perf_metrics = enable_perf_metrics
        self.enable_name_column = enable_name_column
        self.global_columns = global_columns
        self.mode = mode
        self.flush_sec = flush_seconds
        self._handler = None

    def run(self, func, *args, **kwargs):
        try:
            # generate the handler
            self._handler = MetricHandler(self.enable_name_column)
            self._handler.create_metrics(
                self.metric_specs,
                mode=self.mode,
                global_columns=self.global_columns,
            )
            kwargs["metrics"] = self._handler

            # register exporter for the metrics
            if self.instrumentation_key is not None:
                self._handler.connect_insights(
                    self.instrumentation_key,
                    self.callback,
                    enable_standard_metrics=self.perf_metrics,
                    flush_sec=self.flush_sec,
                )
        except Exception as ex:
            logging.error(f"Failed to create Metrics Logger: {ex}")
            raise ex

        return func(*args, **kwargs)

    def teardown(self, *args, **kwargs):
        if self._handler is not None:
            self._handler.shutdown()
