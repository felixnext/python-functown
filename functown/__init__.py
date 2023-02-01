__version__ = "2.0.0"

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
    logging.warning("Unable to load auth, please install `functown[jwt]`")

try:
    from . import serialization
except Exception as ex:
    logging.error(f"Unable to load serialization: {ex}")

try:
    from . import insights
    from .insights import (
        InsightsLogs,
        InsightsMetrics,
        InsightsEvents,
        InsightsTracer,
        insights as Insights,  # avoid name clash with insights package
    )
except Exception as ex:
    logging.warning("Unable to load metrics, please install `functown[insights]`")
