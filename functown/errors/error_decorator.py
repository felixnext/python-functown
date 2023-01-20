"""
Function decorator that should make error handling easier
"""

from types import TracebackType
from typing import List
import os
import sys
import json
import logging

from azure.functions import HttpResponse

from functown.utils import BaseDecorator
from .errors import TokenError, HandlerError, ArgError


class ErrorHandler(BaseDecorator):
    def __init__(
        self,
        debug: bool = False,
        log_all_errors: bool = True,
        return_errors: bool = True,
        enable_logger: bool = True,
        clean_logger: bool = True,
        **kwargs,
    ):
        super().__init__(None, **kwargs)

        # set error handling
        self.debug = debug
        self.log_all_errors = log_all_errors
        self.return_errors = return_errors
        self.enable_logger = enable_logger
        self.clean_logger = clean_logger

    def _send_response(
        self,
        ex: Exception,
        code: int,
        msg: str = None,
        log_error: bool = False,
    ):
        msg = msg if msg else f"Got error: {type(ex)}"
        mime = "text/plain"

        # get additional data
        exc_type, exc_obj, exc_tb = sys.exc_info()
        names = self._get_trace(exc_tb)

        # validate error type to return
        if self.return_errors is True:
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

    def _get_trace(self, tb: TracebackType) -> List[str]:
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

    def run(self, func, *args, **kwargs):
        """Decorator to handle errors

        Note: Since this decorator returns response from the function it is advised to use it
        as the last (outermost) decorator
        """
        # check if logger should be created
        if self.enable_logger:
            try:
                # check for logger
                logger = self._create_logger(self.clean_logger, *args, **kwargs)
                if logger is not None:
                    kwargs["logger"] = logger
            except Exception as ex:
                logging.error(f"Failed to get logger: {ex}")
                raise ex
        else:
            logger = logging

        try:
            # FEAT: check if logger is already passed
            return func(*args, **kwargs)
        except TokenError as ex:
            logger.error("Token Error")
            return self._send_response(
                ex,
                ex.code,
                msg=ex.msg,
                log_error=self.log_all_errors,
            )
        except HandlerError as ex:
            logger.error("Handler Error")
            return self._send_response(
                ex,
                ex.code,
                msg=ex.msg,
                log_error=self.log_all_errors,
            )
        except ArgError as ex:
            logger.error("Argument Error")
            return self._send_response(
                ex,
                ex.code,
                msg=ex.msg,
                log_error=self.log_all_errors,
            )
        except Exception as ex:
            logger.error("General Error")
            return self._send_response(
                ex,
                500,
                msg="This function executed unsuccessfully",
                log_error=self.debug or self.log_all_errors,
            )
