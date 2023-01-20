__version__ = "0.2.0"

import logging

try:
    from . import errors
    from .errors import handle_errors
    from .args import RequestArgHandler
    from .clean_decorator import clean

    from . import auth
except Exception as ex:
    logging.error(f"Not all dependencies installed: {ex}")

try:
    from . import metrics
    from .metrics import log_metrics
except Exception as ex:
    logging.error(f"Unable to load metrics: {ex}")
