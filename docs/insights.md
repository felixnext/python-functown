# Application Insights Metrics

To make sure all dependencies are loaded, please install:

```bash
pip install functown[insights]
```

The exposed functionality of Application Insights can be splitted into four categories.
Each of the categories have their own decorator that exposes the functionality.
However, the combined functionality can also be access through the `Insights` decorator:

```python
from functown.insights import insights, TracerObject, MetricSpec, MetricHandler, MetricType
from functown.utils import get_config

@insights(
    instrumentation_key=get_config("APPIN_KEY"),
    enable_logger=True, enable_events=True, enable_tracer=True, enable_metrics=True,
    metrics=[
        MetricSpec(
            name="my_metric",
            description="My metric",
            aggregation=MetricType.COUNTER,
            interval=TimeSpan(minutes=1),
        )
    ]
)
def main(
    req: HttpRequest,
    logger: Logger,
    events: Logger,
    tracer: TracerObject,
    metrics: MetricHandler,
    **kwargs
) -> HttpResponse:
    # ...
    logger.info("Hello world")
    events.warning("my_event", extra={"custom_dimensions": {"foo": "bar"}})
    metrics["my_metric"].record(1)

    with tracer.span("my_span"):
        # ...
```

## Logging

Logging functionality allows to send logging events directly to application insights.
The code interface for that is provided through `OpenCensus` in the background and
exposed through a `logging.Logger` object.

You can use that `Logger` like you regularly would, but can provide additional tags
that will get logged in Application Insights through
`extra={"custom_dimensions": {...}}`:

```python
from functown.insights import InsightsLogs

@InsightsLogs(instrumentation_key=get_config("APPIN_KEY"))
def main(req: HttpRequest, logger: Logger, **kwargs) -> HttpResponse:
    # ...
    logger.info("Hello world", extra={"custom_dimensions": {"foo": "bar"}})
```

## Event Tracking

Event Tracking allows to send custom events to Application Insights. It works in the
same way as logging, as this also works through a `Logger` object:

```python
from functown.insights import InsightsEvents

@InsightsEvents(get_config("APPIN_KEY"))
def main(req: HttpRequest, events: Logger, **kwargs) -> HttpResponse:
    # ...
    events.warning("my_event", extra={"custom_dimensions": {"foo": "bar"}})
```

## Metrics

Metrics allows to send custom metrics to Application Insights. The metrics are all
accessed through a `MetricHandler` object that is a dictionary-like object that
can also handling co-logging of metrics.

```python
from functown.insights import InsightsMetrics, MetricSpec, MetricType

@InsightsMetrics(
    get_config("APPIN_KEY"),
    metrics=[
        MetricSpec(
            name="my_metric",
            description="My metric",
            unit="Count",
            aggregation=MetricType.GAUGE,
        )
    ]
)
def main(req: HttpRequest, metrics: MetricHandler, **kwargs) -> HttpResponse:
    # ...
    metrics["my_metric"].record(1)
```

As you can see each `Metric` is created through a `MetricSpec` object. This spec
provides the general settings how a metric should behave. In particular it sets the
type:

* `MetricType.COUNTER`: A counter is a cumulative metric that represents a single
    monotonically increasing counter. For example, you can use a counter to represent
    the number of requests served, tasks completed, or errors.
* `MetricType.GAUGE`: A gauge is a metric that represents a single numerical value
    that can arbitrarily go up and down. Gauges are typically used for measured values
    like temperatures or current memory usage, but also "counts" that can go up and
    down, like the number of running goroutines.
* `MetricType.SUM`: A sum is a cumulative metric that represents a single numerical
    value accumulated over a time interval. A sum is considered to be "monotonic" if
    the value can only increase or be reset to zero on restart. For example, you can
    use a sum to track the total number of bytes allocated and deallocated.

Each metric also has a `dtype` (float or int) and a `namespace`. You can put multiple
metrics in the same namespace, in which case they are always logged together. This
should be done through the `record` function of the metric handler:

```python
metrics.record({"metric1": 1, "metric2": 2})
```

If you log these metrics through their respective metric objects (`metrics["my_metric"]`)
it will log a `None` for all remaining metrics in the same namespace.

> **Note:** Azure Functions can keep metrics in memory. So it can be possible that a
> next function call keep the metrics back up. This is intended behavior to optimize
> export flushing to Application Insights.

## Tracing

Tracing allows to send traces to Application Insights. It generates a `TracerObject`
that is a wrapper around the `OpenCensus` tracer object. It allows to create spans
and add additional tags to them:

```python
from functown.insights import InsightsTracer, TracerObject

@InsightsTracer(get_config("APPIN_KEY"))
def main(req: HttpRequest, tracer: TracerObject, **kwargs) -> HttpResponse:
    # ...
    with tracer.span("my_span"):
        # ...
```

## Infrastructure

Make sure to check out the [development guide](dev-guide.md) to see how to setup
the [example Function](../example) and how to view metrics in Application Insights.
