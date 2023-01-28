"""Implements a decorator that allows to stack decorators.

Copyright (c) 2023 Felix Geilert
"""

from typing import List

from .base_decorator import BaseDecorator


class StackDecorator(BaseDecorator):
    """A decorator that allows to stack decorators.

    This can also execute custom functions by overriding the run_pre_hook and
    run_post_hook methods.

    Args:
        stack (List[BaseDecorator]): A list of decorators to apply.
        added_kw (List[str]): A list of keywords that are added by the decorator.
    """

    def __init__(
        self,
        stack: List[BaseDecorator],
        added_kw: List[str] = None,
        **kwargs,
    ):
        # set and expand
        self.__decs = stack
        kws = added_kw or []
        for dec in self.__decs:
            kws.extend(dec.added_kw)

        # init
        super().__init__(None, added_kw=kws, **kwargs)

    def run_pre_hook(self, func, *args, **kwargs):
        """Child classes can override this method to execute a pre hook."""
        return func

    def run_post_hook(self, func, *args, **kwargs):
        """Child classes can override this method to execute a post hook."""
        return func

    def run(self, func, *args, **kwargs):
        # execute pre hook
        func = self.run_pre_hook(func, *args, **kwargs)

        # apply all decorators
        for dec in self.__decs:
            func = dec(func)

        # execute post hook
        func = self.run_post_hook(func, *args, **kwargs)

        return func(*args, **kwargs)
