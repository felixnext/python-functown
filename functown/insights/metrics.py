"""Helper classes for metrics.

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

    def add_default_column(self, key: Any, value: Any):
        """Adds a default tag to the metric.

        Note: These tags are only provided when no specific tags are provided.
        """
        if key not in self.spec.columns:
            logging.warning(
                f"Key {key} is not a valid column for this metric. Ingnoring."
            )
            return
        self.tag.insert(key, value)

    def record(self, value: Union[float, int], columns: Dict[Any, Any] = None):
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
    def time_series(self, dt: datetime = datetime.utcnow()) -> List[Any]:
        """Returns the time series of the metric."""
        # FEAT: update typing here (after unit test)
        data = list(self.map.measure_to_view_map.get_metrics(datetime.utcnow()))
        return data[0].time_series[0]
