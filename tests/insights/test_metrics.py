"""Tests the Metrics Class and spec against local opencensus library

Copyright (c) 2023, Felix Geilert
"""


import pytest
import time

from functown.insights import (
    MetricType,
    MetricSpec,
    MetricTimeValue,
    MetricHandler,
)


def test_handler():
    """Test the MetricHandler class."""
    # assert creation
    handler = MetricHandler()
    assert handler is not None

    # assert singleton
    handler2 = MetricHandler()
    assert handler2 == handler

    # create a metric
    spec = MetricSpec(
        "test_metric", "some metric", "units", ["col1", "col2"], MetricType.COUNTER, int
    )
    handler.create_metrics([spec])

    # assert access types
    m = handler.get_metric("test_metric")
    assert m.spec == spec
    m2 = handler["test_metric"]
    assert m2 == m
    m3 = handler.test_metric
    assert m3 == m


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
                (5.5, {"col2": "foo"}),
            ],
            5.5,
        ),
        (
            "sum_metric",
            ["col2"],
            MetricType.SUM,
            float,
            3.0,
            [
                (1.0, {"col2": "bar"}),
                (0.5, {"col2": "bar"}),
                (3.0, {"col2": "bar"}),
                (4.0, {"col2": "bar"}),
                (5.5, {"col2": "bar"}),
            ],
            17.0,
        ),
    ],
    ids=["counter", "gauge", "sum"],
)
@pytest.mark.skip
def test_metric_counter(name, cols, mtype, dtype, start, values, expected_data):
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
    handler = MetricHandler()
    handler.create_metrics([spec])
    metric = handler[name]

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
    _, tags = values[-1]
    t = ts[-1]
    assert type(t) == MetricTimeValue
    # assert the tags
    assert t.columns["__name"] == name
    if tags and len(unique_cols) == 1:
        for k, v in tags.items():
            assert t.columns[k] == v


@pytest.mark.skip
def test_metric_multi():
    """Tests the MetricSpec class"""
    # define a spec
    specs = [
        MetricSpec(
            name="multi_counter_metric",
            description="first metric",
            unit="count",
            columns=["col1"],
            mtype=MetricType.COUNTER,
            dtype=int,
        ),
        MetricSpec(
            name="multi_gauge_metric",
            description="first metric",
            unit="count",
            columns=["col1"],
            mtype=MetricType.COUNTER,
            dtype=int,
        ),
    ]

    # create a metric
    handler = MetricHandler()
    handler.create_metrics(specs)
    m1 = handler["multi_counter_metric"]
    m2 = handler.multi_gauge_metric

    # record some values in the first metric
    for i in [2, 5, 1, 3, 4]:
        m1.record(i)
        time.sleep(0.2)

    # assert value in the first metric
    assert m1.current_data == 5

    # record some values in the second metric
    for i in [10, 30, 20, 10, 40]:
        m2.record(i)
        time.sleep(0.2)

    # assert value in the second metric
    assert m2.current_data == 40

    # assert value in the first metric again (to see if we can read both)
    assert m1.current_data == 5
