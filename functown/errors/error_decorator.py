"""
Function decorator that should make error handling easier
"""

from types import TracebackType
from typing import List
import os
import sys
import json
import logging

from azure.functions import HttpRequest, HttpResponse

from .errors import TokenError, HandlerError, ArgError


def _send_response(
    ex: Exception,
    code: int,
    msg: str = None,
    return_error: bool = False,
    log_error: bool = False,
):
    msg = msg if msg else f"Got error: {type(ex)}"
    mime = "text/plain"

    # get additional data
    exc_type, exc_obj, exc_tb = sys.exc_info()
    names = _get_trace(exc_tb)

    # validate error type to return
    if return_error == True:
        # update mime type
        mime = "application/json"
        msg = {"user_message": msg}

        # add exception and trace to message
        msg["type"] = str(exc_type)
        msg["value"] = str(exc_obj)
        msg["trace"] = names

        # encode for return
        msg = json.dumps(msg)

    # check for logs
    if log_error is True:
        exc_obj = ex.msg if hasattr(ex, "msg") else exc_obj
        logging.error(f"Error ({exc_type}): {str(ex)} (Obj: {exc_obj})")
        logging.error("Trace:")
        for name in names:
            logging.error(f"- {name}")

    return HttpResponse(msg, status_code=code, mimetype=mime)


def _get_trace(tb: TracebackType) -> List[str]:
    names = []
    while tb:
        file_name = os.path.split(tb.tb_frame.f_code.co_filename)[1]
        fct_line_no = tb.tb_frame.f_code.co_firstlineno
        act_line_no = tb.tb_frame.f_lineno
        names.append(
            f"{file_name}:{fct_line_no}:{act_line_no} - Vars: {tb.tb_frame.f_code.co_varnames}"
        )
        tb = tb.tb_next
    return names


def handle_errors(
    debug: bool = False,
    log_all_errors: bool = False,
    return_errors: bool = False,
    clean_logger: bool = False,
    last_decorator: bool = False,
):
    """Decorator to handle errors

    Note: Since this decorator returns response from the function it is advised to use it
    as the last (outermost) decorator

    Args:
        debug: Defines of errors should be printed only for code fails
        log_all_errors: Defines if all error messages should be displayed in detail in the logs
        return_errors: Defines if the error trace should be returned in the response
    """

    def handle_fct(function):
        def execute(req: HttpRequest, *params, **kwargs) -> HttpResponse:
            # FEAT: generate logger for code
            try:
                # check for logger
                logger = kwargs.get("logger", None)
                if logger is not None:
                    del kwargs["logger"]
                if logger is None or clean_logger is True:
                    logging.debug(f"Creating logger for {function.__name__}")
                    logger = logging.getLogger(__name__)
            except Exception as ex:
                logging.error(f"Failed to get logger: {ex}")
                raise ex

            try:
                # FEAT: check if logger is already passed
                return function(req, logger=logger, *params, **kwargs)
            except TokenError as ex:
                logging.error("Token Error")
                return _send_response(
                    ex,
                    ex.code,
                    msg=ex.msg,
                    return_error=return_errors,
                    log_error=log_all_errors,
                )
            except HandlerError as ex:
                logging.error("Handler Error")
                return _send_response(
                    ex,
                    ex.code,
                    msg=ex.msg,
                    return_error=return_errors,
                    log_error=log_all_errors,
                )
            except ArgError as ex:
                logging.error("Argument Error")
                return _send_response(
                    ex,
                    ex.code,
                    msg=ex.msg,
                    return_error=return_errors,
                    log_error=log_all_errors,
                )
            except Exception as ex:
                logging.error("General Error")
                return _send_response(
                    ex,
                    500,
                    msg="This function executed unsuccessfully",
                    return_error=return_errors,
                    log_error=debug or log_all_errors,
                )

        # check for last decorator
        if last_decorator is True:
            return lambda req: execute(req)
        return execute

    return handle_fct
