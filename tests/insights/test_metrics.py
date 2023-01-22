"""Tests the Metrics Class and spec against local opencensus library

Copyright (c) 2023, Felix Geilert
"""


from opencensus.stats import stats as stats_module
import pytest
import time

from functown.insights import Metric, MetricType, MetricSpec, MetricTimeValue


# create a fixture for the view manager
@pytest.fixture(scope="session", autouse=True, name="view_manager")
def view_manager():
    """Creates a view manager for the tests"""
    stats = stats_module.stats
    view_manager = stats.view_manager
    yield view_manager
    view_manager.clear()


@pytest.mark.parametrize(
    "name, cols, mtype, dtype, start, values, expected_data",
    [
        (
            "counter_metric",
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
            "gauge_metric",
            ["col2"],
            MetricType.GAUGE,
            float,
            0.5,
            [
                (1.0, {"col2": "foo"}),
                (2.0, {"col2": "foo"}),
                (3.0, {"col2": "foo"}),
                (4.0, {"col2": "foo"}),
                (5.0, {"col2": "foo"}),
            ],
            5.0,
        ),
    ],
    ids=["counter", "gauge"],
)
# TODO: fix this test
@pytest.mark.skip
def test_metric_counter(
    name, cols, mtype, dtype, start, values, expected_data, view_manager
):
    """Tests the MetricSpec class"""
    # define a spec
    spec = MetricSpec(
        name=name,
        description="My metric",
        unit="count",
        columns=cols,
        mtype=mtype,
        dtype=dtype,
        start_value=start,
    )

    # create a metric
    metric = Metric(spec, view_manager)

    # log values
    unique_cols = set()
    for v, cols in values:
        metric.record(v, cols)
        unique_cols.add(str(cols))
        time.sleep(0.5)

    # retrieve data
    data = metric.current_data
    ts = metric.full_time_series

    # assert data
    if mtype == MetricType.COUNTER:
        assert len(data) == len(unique_cols)
    else:
        assert len(data) == 1
    for d in data:
        assert type(d) == dtype
    assert data[0] == expected_data

    # assert data
    assert len(ts) == len(unique_cols)
    for t in ts:
        assert type(t) == MetricTimeValue
