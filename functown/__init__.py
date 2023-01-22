__version__ = "1.0.0"

import logging

try:
    from . import errors
    from .errors import ErrorHandler
    from .args import RequestArgHandler
    from . import utils

    from . import auth
except Exception as ex:
    logging.error(f"Not all dependencies installed: {ex}")

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
