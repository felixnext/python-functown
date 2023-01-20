"""Simple Decorator to clean main function for outer calls.

FEAT: Integrate a callable class abstraction to avoid the clean decorator at the outmost layer?

Copyright (c) 2023, Felix Geilert
"""

from azure.functions import HttpRequest, HttpResponse


def clean(function):
    """Decorator that cleans the *param and **kwargs from the function."""

    def execute(req: HttpRequest, *params, **kwargs) -> HttpResponse:
        return function(req, *params, **kwargs)

    return lambda req: execute(req)
