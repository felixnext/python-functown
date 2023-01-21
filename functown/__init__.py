__version__ = "1.0.0"

import logging

try:
    from . import errors
    from .errors import ErrorHandler
    from .args import RequestArgHandler
    from .utils.clean_decorator import clean
    from . import utils

    from . import auth
except Exception as ex:
    logging.error(f"Not all dependencies installed: {ex}")

try:
    from . import insights
    from .insights import InsightsLogHandler, InsightsHandler
    from .insights import metrics_all, metrics_logger, metrics_events, metrics_tracer
except Exception as ex:
    logging.error(f"Unable to load metrics: {ex}")
