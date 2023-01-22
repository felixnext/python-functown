"""Tests the Metrics Class and spec against local opencensus library

Copyright (c) 2023, Felix Geilert
"""


from opencensus.stats import stats as stats_module
import pytest
import time

from functown.insights import Metric, MetricType, MetricSpec, MetricTimeValue


@pytest.mark.parametrize(
    "cols, mtype, dtype, start, values, expected_data",
    [
        (
            ["col1"],
            MetricType.COUNTER,
            int,
            0,
            [
                (1, None),
                (2, {"col1": "foo"}),
                (3, {"col1": "bar"}),
                (4, None),
                (5, {"col1": "foo"}),
            ],
            2,
        ),
        (
            ["col1"],
            MetricType.GAUGE,
            float,
            0.5,
            [
                (1.0, {"col1": "foo"}),
                (2.0, {"col1": "foo"}),
                (3.0, {"col1": "foo"}),
                (4.0, {"col1": "foo"}),
                (5.0, {"col1": "foo"}),
            ],
            5.0,
        ),
    ],
    ids=["counter", "gauge"],
)
def test_metric_spec(cols, mtype, dtype, start, values, expected_data):
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
    unique_cols = set()
    for v, cols in values:
        metric.record(v, cols)
        unique_cols.add(str(cols))
        time.sleep(0.5)

    # retrieve data
    data = metric.current_data

    # assert data
    if mtype == MetricType.COUNTER:
        assert len(data) == len(unique_cols)
    else:
        assert len(data) == 1
    for d in data:
        assert type(d) == dtype
    assert data[0] == expected_data

    # retrieve time_series
    ts = metric.full_time_series

    # assert data
    assert len(ts) == len(unique_cols)
    for t in ts:
        assert type(t) == MetricTimeValue
