"""Helper classes for metrics.

Note that the time_series returned from OpenCensus internally do not always reflect
the correct timestamps, but are bucketed. Therefore items can cluster together.

Copyright (c) 2023, Felix Geilert
"""


from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Dict, Union, Type, List, Any

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.metrics.export.metric import Metric as OCMetric
from opencensus.metrics.export.time_series import TimeSeries as OCTimeSeries


class MetricType(Enum):
    """The type of the metric."""

    COUNTER = 1
    GAUGE = 2
    SUM = 3


@dataclass
class MetricSpec:
    """A definition of a metric.

    Args:
        name (str): The name of the metric.
        description (str): The description of the metric.
        unit (str): The unit of the metric.
        aggregation (Aggregation): The aggregation of the metric.
    """

    name: str
    description: str
    unit: str
    columns: List[str]
    mtype: MetricType
    dtype: Type[Union[int, float]] = int
    start_value: Union[int, float, None] = None


@dataclass
class MetricTimeValue:
    """A value for a metric at a specific time.

    Args:
        value (Union[int, float]): The value of the metric.
        timestamp (datetime): The timestamp of the value.
        columns (Dict[str, Any]): The columns of the metric.
    """

    value: Union[int, float]
    timestamp: datetime
    columns: Dict[str, Any]

    def __str__(self):
        return f"{self.value} at {self.timestamp} with {self.columns}"


class Metric:
    """Handler class for metrics that allow to record values"""

    def __init__(
        self,
        spec: MetricSpec,
        vm: stats_module.ViewManager,
    ):
        # store the spec
        self.spec = spec

        # select the measure
        measure = {
            float: measure_module.MeasureFloat,
            int: measure_module.MeasureInt,
        }[spec.dtype]

        # select the aggregation
        agg = {
            MetricType.COUNTER: aggregation_module.CountAggregation,
            MetricType.GAUGE: aggregation_module.LastValueAggregation,
            MetricType.SUM: aggregation_module.SumAggregation,
        }[spec.mtype]

        # generate data
        self.measure = measure(spec.name, spec.description, spec.unit)
        self.view = view_module.View(
            f"{spec.name}_view",
            spec.description,
            spec.columns,
            self.measure,
            agg() if spec.start_value is None else agg(spec.start_value),
        )
        vm.register_view(self.view)
        self.map = stats_module.stats.stats_recorder.new_measurement_map()
        self.tag = tag_map_module.TagMap()

    def add_default_column(self, key: str, value: Any):
        """Adds a default tag to the metric.

        Note: These tags are only provided when no specific tags are provided.
        """
        if key not in self.spec.columns:
            logging.warning(
                f"Key {key} is not a valid column for this metric. Ingnoring."
            )
            return
        self.tag.insert(key, value)

    def record(self, value: Union[float, int], columns: Dict[str, Any] = None):
        """Records a value for the metric."""
        # generate the tags
        tag_map = self.tag
        if columns is not None:
            tag_map = tag_map_module.TagMap()
            for key, cval in columns.items():
                if key not in self.spec.columns:
                    logging.warning(
                        f"Key {key} is not a valid column for this metric. Ignoring."
                    )
                    continue
                tag_map.insert(key, cval)

        # check if value is float, int or str
        if isinstance(value, float):
            self.map.measure_float_put(self.measure, value)
        elif isinstance(value, int):
            self.map.measure_int_put(self.measure, value)
        else:
            raise ValueError(f"Value {value} is not a valid value.")
        self.map.record(tag_map)

    @property
    def current_data(self) -> List[Union[int, float]]:
        """Returns the data of the metric.

        Note that this will not return timestamps or columns.
        It is also derived from all combined data.

        In case of gauge and sum only the last value is returned (List of size 1).
        """
        # check the type
        if self.spec.mtype in (MetricType.GAUGE, MetricType.SUM):
            return [self.full_time_series[-1].value]

        # retrieve the overall data
        return [dp.value for dp in self.full_time_series]

    @property
    def full_time_series(self) -> List[MetricTimeValue]:
        """Retrieves the entire time series of the data.

        Note that each column combination is set into a new time series.

        This structure will combine the regarding time series into a single
        (with column values attached to each object)
        """
        return self.get_time_series()

    def get_time_series(
        self,
        start: datetime = None,
        end: datetime = None,
        columns: Dict[str, Any] = None,
    ) -> List[MetricTimeValue]:
        """Returns the timeseries data of this metric filter to specifications.

        Args:
            start (datetime): The start time of the data. If None, all data is returned.
                Defaults to None.
            end (datetime): The end time of the data. If None, the current time is used.
                Defaults to None.
            columns (Dict[str, Any]): The columns to filter for. If None, all columns
                are returned. Defaults to None.

        Returns:
            List[MetricTimeValue]: The time series data.
        """
        # update the datetimes
        if end is None:
            end = datetime.utcnow()
        if start is None:
            start = datetime.min

        # retrieve the overall data
        data: List[OCMetric] = list(self.map.measure_to_view_map.get_metrics(end))
        # retrieve the time series data
        # NOTE: each new tag configuration will create a new time-series
        series: List[OCTimeSeries] = data[0].time_series

        # combine the time series and map them
        if columns is not None:
            # filter timeseries (based on label_values)
            vals = [columns.get(col, None) for col in self.spec.columns]
            series = [s for s in series if s.label_values == vals]

        # filter and convert the data
        items = []
        for serie in series:
            vals = {
                col: val.value
                for col, val in zip(self.spec.columns, serie.label_values)
            }
            items += [
                MetricTimeValue(p.value.value, p.timestamp, vals)
                for p in serie.points
                if start <= p.timestamp <= end
            ]

        # sort data by timestamp
        items.sort(key=lambda x: x.timestamp)
        return items
