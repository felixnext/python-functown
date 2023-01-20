"""Simple Decorator to clean main function for outer calls.

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest, HttpResponse


def clean():
    def handle_fct(function):
        def execute(req: HttpRequest, *params, **kwargs) -> HttpResponse:
            return function(req, *params, **kwargs)

        return lambda req: execute(req)

    return handle_fct
