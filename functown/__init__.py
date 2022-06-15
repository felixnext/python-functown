
__version__ = "0.1.3"

import logging

try:
    from . import errors
    from .errors import handle_errors
    from .args import RequestArgHandler

    from . import auth
except Exception as ex:
    logging.error(f"Not all dependencies installed: {ex}")
