"""Tests the Metrics Class and spec against local opencensus library

Copyright (c) 2023, Felix Geilert
"""


from opencensus.stats import stats as stats_module
import pytest

from functown.insights import Metric, MetricType, MetricSpec


@pytest.mark.parametrize(
    "cols, mtype, dtype, start, values",
    [
        (
            ["col1"],
            MetricType.COUNTER,
            int,
            0,
            [(1, None), (2, {"col1": "foo"}), (3, {"col1": "bar"})],
        ),
    ],
    ids=["counter"],
)
def test_metric_spec(cols, mtype, dtype, start, values):
    """Tests the MetricSpec class"""
    # define a spec
    spec = MetricSpec(
        name="my_metric",
        description="My metric",
        unit="count",
        columns=cols,
        mtype=mtype,
        dtype=dtype,
        start_value=start,
    )

    # create a view manager
    vm = stats_module.stats.view_manager

    # create a metric
    metric = Metric(spec, vm)

    # log values
    for v, cols in values:
        metric.record(v, cols)

    # retrieve data
    data = metric.time_series

    # assert data
    assert len(data) == len(values)
