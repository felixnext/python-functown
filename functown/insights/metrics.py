"""Helper classes for metrics.

Copyright (c) 2023, Felix Geilert
"""


from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union, Type


class MetricType(Enum):
    """The type of the metric."""

    COUNTER = 1
    """A counter metric."""
    GAUGE = 2
    """A gauge metric."""
    SUM = 3
    """A sum metric."""


class Metric:
    """Handler class for metrics that allow to record values"""

    def __init__(self):
        pass

    def record(self, value: Union[float, int], tags: Dict = None):
        pass


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
    mtype: MetricType
    dtype: Type[Union[int, float]]

    # def _create_metric()
