'''
Function decorator that should make error handling easier
'''

import os
import sys
import logging

from azure.functions import HttpRequest, HttpResponse

from .errors import TokenError, HandlerError, ArgError


def handle_errors(debug=False, show_all_errors=False):
    '''Decorator to handle errors

    Args:
        debug: Defines of errors should be printed only for code fails
        show_all_errors: Defines if errors should be printed out to console (no matter source)
    '''
    def handle_fct(function):
        def execute(req: HttpRequest) -> HttpResponse:
            try:
                return function(req)
            except TokenError as ex:
                logging.error("Token Error")
                if show_all_errors:
                    logging.error(ex)
                return HttpResponse(ex.msg, status_code=ex.code)
            except HandlerError as ex:
                logging.error("Handler Error")
                if show_all_errors:
                    logging.error(ex)
                return HttpResponse(ex.msg, status_code=ex.code)
            except ArgError as ex:
                logging.error("Argument Error")
                if show_all_errors:
                    logging.error(ex)
                return HttpResponse(ex.msg, status_code=ex.code)
            except Exception as ex:
                logging.error("General Error")
                if debug or show_all_errors:
                    # provide more detailed logging info
                    exc_type, exc_obj, exc_tb = sys.exc_info()

                    # properly retrieve trace
                    names = []
                    tb = exc_tb
                    while tb:
                        file_name = os.path.split(tb.tb_frame.f_code.co_filename)[1]
                        fct_line_no = tb.tb_frame.f_code.co_firstlineno
                        act_line_no = tb.tb_frame.f_lineno
                        names.append(f"{file_name}:{fct_line_no}:{act_line_no} - Vars: {tb.tb_frame.f_code.co_varnames}")
                        tb = tb.tb_next

                    # print the error
                    exc_obj = ex.msg if hasattr(ex, 'msg') else exc_obj
                    logging.error(f"Error ({exc_type}): {str(ex)} (Obj: {exc_obj})")
                    logging.error("Trace:")
                    for name in names:
                        logging.error(f"- {name}")
                return HttpResponse(u"This function executed unsuccessfully.", status_code=500)

        return execute
    return handle_fct
