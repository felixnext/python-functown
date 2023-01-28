__version__ = "1.1.0"

import logging

try:
    from . import utils
    from . import errors
    from .errors import ErrorHandler
    from .args import RequestArgHandler, ArgsHandler
except Exception as ex:
    logging.error(f"Not all dependencies installed: {ex}")

try:
    from . import auth
    from .auth import AuthHandler
except Exception as ex:
    logging.error(f"Unable to load auth: {ex}")

try:
    from . import insights
    from .insights import (
        InsightsLogs,
        InsightsMetrics,
        InsightsEvents,
        InsightsTracer,
        Insights,
    )
except Exception as ex:
    logging.error(f"Unable to load metrics: {ex}")
