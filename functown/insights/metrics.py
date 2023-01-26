"""Helper classes for metrics.

Note that the time_series returned from OpenCensus internally do not always reflect
the correct timestamps, but are bucketed. Therefore items can cluster together.

This code should provide the primary abstraction interface for OpenCensus API.
No code outside this file should need to touch the opencensus API directly.

Copyright (c) 2023, Felix Geilert
"""


from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Dict, Union, Type, List, Any, Callable

from opencensus.ext.azure import metrics_exporter
from opencensus.stats.measurement_map import MeasurementMap
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.metrics.export.metric import Metric as OCMetric
from opencensus.metrics.export.time_series import TimeSeries as OCTimeSeries

from functown.utils.metaclasses import ThreadSafeSingleton


class MetricType(Enum):
    """The type of the metric."""

    COUNTER = 1
    GAUGE = 2
    SUM = 3


class MetricUseMode(Enum):
    """The use mode of the metric."""

    HARD_FAIL = 1
    """Hard Fail in the case of a namespace conflict"""
    SOFT_FAIL = 2
    """Soft Fail in the case of a namespace conflict"""
    OVERWRITE = 3
    """Overwrite in the case of a namespace conflict"""
    REUSE = 4
    """Reuse in the case of a namespace conflict"""


@dataclass
class MetricSpec:
    """A definition of a metric.

    Define namespaces if you have co-dependent metrics that you want to always record
    together.

    Args:
        name (str): The name of the metric.
        description (str): The description of the metric.
        unit (str): The unit of the metric.
        columns (List[str]): The columns of the metric. These will be used to
            log additional data into the metric. Note that metric values aggregations
            happens based on a group by these columns (and timestamps).
        mtype (MetricType): The type of the metric. Defines how data logged is
            aggregated.
        dtype (Type[Union[int, float]]): The data type of the metric. Defaults to int.
        namespace (str): The namespace of the metric. Metrics in the same namespace will
            be recorded together. Note that this might lead to increases in counter
            metrics (as None values are logged that are counted). Per default every
            metric is in its own namespace.
    """

    name: str
    description: str
    unit: str
    columns: List[str]
    mtype: MetricType
    dtype: Type[Union[int, float]] = int
    namespace: str = None
    start_value: Union[int, float, None] = None

    @property
    def used_namespace(self) -> str:
        """The namespace that is used for the metric.

        If no namespace is defined, the name is used.
        """
        if self.namespace is None:
            return self.name
        return self.namespace


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
    """Handler class for metrics that allow to record values

    Args:
        spec (MetricSpec): The specification of the metric.
        vm (stats_module.ViewManager): The view manager.
        map (MeasurementMap): The measurement map (should it be reused).
        add_name_column (bool): Whether to add the name of the metric as a column.
        handler_columns (Dict[str, Any]): Additional columns specified by the handler.
            These will always be added to the metric if set. Defaults to None.
    """

    _NAME_COL = "__name"

    def __init__(
        self,
        spec: MetricSpec,
        vm: stats_module.ViewManager,
        map: MeasurementMap,
        add_name_column: bool = True,
        handler_columns: Dict[str, Any] = None,
    ):
        # store the spec
        self.spec = spec
        self.map = map
        self.add_name_column = add_name_column
        self.required_columns = handler_columns or {}

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

        # generate the columns
        cols = spec.columns or []
        if add_name_column:
            cols = [self._NAME_COL] + cols
        cols += list(self.required_columns.keys())
        # remove duplicates (preserving order)
        cols = list(dict.fromkeys(cols))

        # generate data
        self.measure = measure(spec.name, spec.description, spec.unit)
        self.view = view_module.View(
            self.__view_name,
            spec.description,
            cols,
            self.measure,
            agg() if spec.start_value is None else agg(spec.start_value),
        )
        vm.register_view(self.view)

        # generate the default tag map
        self.tag = self.__build_tag_map({})

    @property
    def __view_name(self):
        return f"{self.spec.name}_view"

    def __build_tag_map(self, columns: Dict[str, Any]) -> tag_map_module.TagMap:
        """Builds a tag map from the columns."""
        tag = tag_map_module.TagMap()
        if self.add_name_column:
            tag.insert(self._NAME_COL, self.spec.name)

        # add the required columns (ordering is important)
        # note that user columns overwrite required columns
        cols = {**self.required_columns, **columns}
        for key, value in cols.items():
            if key not in self.spec.columns:
                logging.warning(
                    f"Key {key} is not a valid column for metric {self.sepc.name}. "
                    "Ignoring."
                )
                continue
            tag.insert(key, value)
        return tag

    def add_default_column(self, key: str, value: Any, persistent: bool = False):
        """Adds a default tag to the metric.

        Note: These tags are only provided when no specific tags are provided.

        Args:
            key (str): The key of the tag.
            value (Any): The value of the tag.
            persistent (bool): Persistent columns are always added to the record,
                even if user-specified columns are provided. Defaults to False.
        """
        # ensure that the key is specified
        if key not in self.spec.columns:
            logging.warning(
                f"Key {key} is not a valid column for this metric. Ingnoring."
            )
            return
        self.tag.insert(key, value)
        if persistent:
            self.required_columns[key] = value

    def _record_measure_only(self, value: Union[float, int]):
        """Records a value for the metric."""
        # generate the tags
        if isinstance(value, float):
            self.map.measure_float_put(self.measure, value)
        elif isinstance(value, int):
            self.map.measure_int_put(self.measure, value)
        else:
            raise ValueError(f"Value {value} is not a valid value.")

    def record(self, value: Union[float, int], columns: Dict[str, Any] = None):
        """Records a value for the metric."""
        # generate the tags
        tag_map = self.tag if columns is None else self.__build_tag_map(columns)

        # measure the value and record it to a feature map
        self._record_measure_only(value)
        self.map.record(tag_map)

    @property
    def current_data(self) -> Union[List[Union[int, float]], None]:
        """Returns the data of the metric.

        Note that this will not return timestamps or columns.
        It is also derived from all combined data.

        Returns:
            List of data. In case of gauge and sum only the last value is returned
            (List of size 1). If no data is available, None is returned.
        """
        # retrieve the overall data
        fts = self.full_time_series

        # check if data is available
        if len(fts) == 0:
            return None

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
        data = [d for d in data if d.descriptor.name == self.__view_name]
        if len(data) == 0:
            return []
        series: List[OCTimeSeries] = data[0].time_series

        # filter timeseries (based on label_values)
        if columns is not None:
            vals = ([self.spec.name] if self.add_name_column else []) + [
                columns.get(col, None) for col in self.spec.columns
            ]
            series = [s for s in series if [lv.value for lv in s.label_values] == vals]
        elif self.add_name_column:
            # in any case filter for the name
            series = [s for s in series if s.label_values[0].value == self.spec.name]

        # filter and convert the data
        items = []
        for serie in series:
            vals = {
                col: val.value
                for col, val in zip(
                    ([self._NAME_COL] if self.add_name_column is True else [])
                    + self.spec.columns,
                    serie.label_values,
                )
            }
            items += [
                MetricTimeValue(p.value.value, p.timestamp, vals)
                for p in serie.points
                if start <= p.timestamp <= end
            ]

        # sort data by timestamp
        items.sort(key=lambda x: x.timestamp)
        return items


class MetricHandler(metaclass=ThreadSafeSingleton):
    def __init__(self, add_name_column: bool = True):
        # create internal data
        self._metrics: Dict[str, Metric] = {}
        self._enable_standard_metrics = True
        self._add_name_column = add_name_column
        self._maps: Dict[str, MeasurementMap] = {}

        # create opencensus data
        self._vm = stats_module.stats.view_manager
        self._exporter: metrics_exporter.MetricsExporter = None

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            try:
                return self._metrics[name]
            except KeyError:
                raise AttributeError(name)

    def __getitem__(self, key):
        # allow ["metric"] retrieval
        return self.get_metric(key)

    def get_metric(self, name: str) -> Union[Metric, None]:
        """Returns the metric with the given name.

        Args:
            name (str): The name of the metric.

        Returns:
            Metric: The metric.
        """
        return self._metrics.get(name, None)

    def create_metrics(
        self,
        specs: List[MetricSpec],
        mode: MetricUseMode = MetricUseMode.HARD_FAIL,
        global_columns: Dict[str, Any] = None,
    ) -> bool:
        """Creates a list of metrics based on the specifications.

        Args:
            specs (List[MetricSpec]): The specifications to create the metrics for.
            mode (MetricUseMode): The mode to use when creating the metrics.
            global_columns (Dict[str, Any]): The global columns to add to all metrics.
                Defaults to None.

        Returns:
            bool: Whether the metrics were created successfully.
        """
        # remove items that are already created
        if mode == MetricUseMode.REUSE:
            dropped = [spec.name for spec in specs if spec.name in self._metrics]
            if len(dropped) > 0:
                logging.info(f"Reusing metrics: {', '.join(dropped)}")
                specs = [spec for spec in specs if spec.name not in self._metrics]

        # check if metric names are valid
        if mode in [MetricUseMode.HARD_FAIL, MetricUseMode.SOFT_FAIL]:
            for spec in specs:
                # check for error
                if spec.name in self._metrics or spec.name in self.__dict__:
                    if mode == MetricUseMode.HARD_FAIL:
                        raise ValueError(
                            f"Metric {spec.name} generates a namespace conflict."
                        )
                    return False
        else:
            dropped = [spec.name for spec in specs if spec.name in self.__dict__]
            if len(dropped) > 0:
                logging.info(f"Dropping metrics (illegal names): {', '.join(dropped)}")
                specs = [spec for spec in specs if spec.name not in self.__dict__]

        # find all namespaces and create maps
        namespaces = set([spec.used_namespace for spec in specs])
        for ns in namespaces:
            if ns not in self._maps:
                self._maps[ns] = stats_module.stats.stats_recorder.new_measurement_map()

        # only create metrics if all are valid
        for spec in specs:
            self._metrics[spec.name] = Metric(
                spec,
                self._vm,
                self._maps[spec.used_namespace],
                add_name_column=self._add_name_column,
                handler_columns=global_columns,
            )

        return True

    def record(self, values: Dict[str, Any], columns: Dict[str, Any] = None):
        """Records the given values to the metrics.

        In this case the values for all metrics are recorded under the same tag-map

        NOTE: This will ignore tags set by individual metrics. (Including default tags).

        Args:
            values (Dict[str, Any]): The values to record.
            columns (Dict[str, Any]): The columns to record the values under.
        """
        # generate tag_map
        tag_map = tag_map_module.TagMap()
        if self._add_name_column:
            tag_map.insert(self._NAME_COL, "global")
        for key, value in (columns or {}).items():
            if key == self._NAME_COL:
                raise ValueError(f"Column {key} is reserved.")
            tag_map.insert(key, value)

        # measure the values
        namespaces = []
        for name, value in values.items():
            if name not in self._metrics:
                raise ValueError(f"Metric {name} does not exist.")
            self._metrics[name]._record_measure_only(value)
            namespaces.append(self._metrics[name].spec.used_namespace)

        # complete recording
        for ns in set(namespaces):
            self._maps[ns].record(tag_map)

    @property
    def is_insights_enabled(self) -> bool:
        """Returns whether the exporter is connected to Application Insights."""
        return self._exporter is not None

    def connect_insights(
        self,
        instrumentation_key: str,
        callback: Callable[[metrics_exporter.Envelope], bool],
        enable_standard_metrics: bool = None,
        flush_sec: float = 15,
    ):
        """Connects the metrics to Azure Insights.

        Args:
            instrumentation_key (str): The instrumentation key to connect to.
            callback (Callable[[metrics_exporter.Envelope], bool]): The callback to
                filter the metrics.
            enable_standard_metrics (bool, optional): Whether to enable standard metrics.
                Defaults to None.
            flush_sec (float, optional): The interval to flush the metrics.
                Defaults to 15.
        """
        # update the metrics
        metrics = enable_standard_metrics
        if metrics is None:
            metrics = self._enable_standard_metrics
        self._enable_standard_metrics = metrics

        # generate exporter
        self._exporter = metrics_exporter.new_metrics_exporter(
            enable_standard_metrics=metrics,
            connection_string=f"InstrumentationKey={instrumentation_key}",
            export_interval=flush_sec,
        )

        # check for filter
        if callback is not None:
            self._exporter.add_telemetry_processor(callback)

        self._vm.register_exporter(self._exporter)

    def shutdown(self):
        """Flushes remaining data."""
        if self._exporter is not None:
            self._exporter.shutdown()
